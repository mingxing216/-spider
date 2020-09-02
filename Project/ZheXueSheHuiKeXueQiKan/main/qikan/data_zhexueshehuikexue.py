# -*- coding:utf-8 -*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import traceback
import hashlib
import random
import re
import requests
from datetime import datetime
from contextlib import closing
import json
import threading
from io import BytesIO
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


log_file_dir = 'SheHuiKeXue'  # LOG日志存放路径
LOGNAME = '<国家哲学社会科学_期刊_data>'  # LOG名
NAME = '国家哲学社会科学_期刊_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

        self.profile_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperInfo'

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges)
            if resp and resp.headers['Content-Type'].startswith('text'):
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    # 存储图片
    def img(self, img_dict):
        # 获取图片响应
        media_resp = self.__getResp(url=img_dict['url'], method='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_dict['url']))
            return

        img_content = media_resp.content
        # 存储图片
        sto = self.dao.saveMediaToHbase(media_url=img_dict['url'], content=img_content, item=img_dict, type='image')
        if sto:
            return True
        else:
            return

    def handle(self, task_data, save_data):
        print(task_data)
        url = task_data.get('url')
        id = re.findall(r"cn/(\w+)/?", url)[0]
        print(id)
        key = 'nssd.org|' + id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()
        xueKeLeiBie = task_data.get('s_xuekeleibie')

        # 获取期刊详情页
        profile_resp = self.__getResp(url=url, method='GET')
        if not profile_resp:
            LOGGING.error('详情页响应失败, url: {}'.format(url))
            return

        profile_text = profile_resp.text

        # ========================== 获取期刊实体 ============================

        # 获取标题
        save_data['title'] = self.server.getJournalTitle(profile_text)
        # 获取英文标题
        save_data['parallel_title'] = {}
        save_data['parallel_title']['text'] = self.server.getParallelTitle(profile_text)
        save_data['parallel_title']['lang'] = "en"
        # 获取封面图片
        save_data['cover'] = self.server.getCover(profile_text)
        # 存储图片
        if save_data['cover']:
            img_dict = {}
            img_dict['url'] = save_data['cover']
            img_dict['bizTitle'] = save_data['title']
            img_dict['relEsse'] = self.server.rela_journal(url=url, key=key, sha=sha)
            img_dict['relPics'] = {}

            self.img(img_dict=img_dict)

        # 获取简介
        save_data['abstract'] = {}
        save_data['abstract']['text'] = self.server.getAbstract(profile_text)
        if save_data['abstract']['text']:
            hasChinese = self.server.hasChinese(save_data['abstract']['text'])
            if hasChinese:
                save_data['abstract']['lang'] = "zh"
            else:
                save_data['abstract']['lang'] = "en"
        else:
            save_data['abstract']['lang'] = ""
        # 主管单位
        save_data['governing_body'] = self.server.getOneValue(profile_text, '主管单位')
        # 主办单位
        save_data['responsible_organization'] = self.server.getMoreValues(profile_text, '主办单位')
        # 社长
        save_data['president'] = self.server.getOneValue(profile_text, '社　　长')
        # 主编
        save_data['chief_editor'] = self.server.getOneValue(profile_text, '主　　编')
        # 创刊时间
        shiJian = self.server.getOneValue(profile_text, '创刊时间')
        if shiJian:
            try:
                save_data['starting_time'] = timeutils.getDateTimeRecord(shiJian)

            except:
                save_data['starting_time'] = shiJian
        else:
            save_data['starting_time'] = ""
        # 出版周期
        save_data['interval_of_issue'] = self.server.getOneValue(profile_text, '出版周期')
        # 地址
        save_data['address'] = self.server.getOneValue(profile_text, '地　　址')
        # 邮编
        save_data['postal_code'] = self.server.getOneValue(profile_text, '邮政编码')
        # 电话
        save_data['telephone'] = self.server.getTelephone(profile_text)
        # 电子邮件
        save_data['email'] = self.server.getHref(profile_text, '电子邮件')
        # 期刊网址
        save_data['journal_website'] = self.server.getHref(profile_text, '期刊网址')
        # ISSN
        issn = self.server.getOneValue(profile_text, '国际标准刊号')
        if issn:
            save_data['issn'] = re.findall(r"ISSN\s*(.*)", issn)[0]
        else:
            save_data['issn'] = ""
        # CN
        cn = self.server.getOneValue(profile_text, '国内统一刊号')
        if cn:
            save_data['cn'] = re.findall(r"CN\s*(.*)", cn)[0]
        else:
            save_data['cn'] = ""
        # 邮发代号
        save_data['issuing_code'] = self.server.getOneValue(profile_text, '邮发代号')
        # 价格
        save_data['price'] = {}
        save_data['price']['unit_price'] = self.server.getOneValue(profile_text, '单　　价')
        save_data['price']['total_price'] = self.server.getOneValue(profile_text, '总　　价')
        # 描述
        save_data['describe'] = {}
        save_data['describe']['history'] = self.server.getHistory(profile_text, '期刊变更')
        honors = self.server.getHonors(profile_text)
        if honors:
            save_data['describe']['honors'] = '该刊已选入：' + honors
        else:
            save_data['describe']['honors'] = ""
        #被收录数据库
        save_data['databases'] = self.server.getDatabases(profile_text)
        # 学科分类
        save_data['subject_classification_name'] = xueKeLeiBie
        # 期刊学术评价
        evaluate_url = self.server.getEvaluateUrl(profile_text)
        if evaluate_url:
            # 请求评价页面，获取响应
            evaluate_resp = self.__getResp(url=evaluate_url, method='GET')
            if not evaluate_resp:
                LOGGING.error('学术评价页响应失败, url: {}'.format(evaluate_url))
                return

            evaluate_text = evaluate_resp.text
            save_data['the_number_of_published_articles_in_journal'] = self.server.getEvaluate(evaluate_text)
        else:
            save_data['the_number_of_published_articles_in_journal'] = []

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = key
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '期刊'
        # 生成es ——栏目名称
        save_data['es'] = '期刊'
        # 生成ws ——目标网站
        save_data['ws'] = '国家哲学社会科学学术期刊数据库'
        # 生成clazz ——层级关系
        save_data['clazz'] = '期刊_学术期刊'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_论文'
        # 生成ref
        save_data['ref'] = ''
        # 采集责任人
        save_data['creator'] = '张明星'
        # 更新责任人
        save_data['modified_by'] = ''
        # 采集服务器集群
        save_data['cluster'] = 'crawler'
        # 元数据版本号
        save_data['metadata_version'] = 'V1.1'
        # 采集脚本版本号
        save_data['script_version'] = 'V1.3'

    def run(self):
        #第一次请求的等待时间
        delay_time = time.time()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        LOGGING.info('handle | download delay | use time: {}s'.format('%.3f' % (time.time() - delay_time)))
        # 单线程无限循环
        while True:
            # 获取任务
            start_time = time.time()
            task_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE, count=1,
                                         lockname=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE_LOCK)
            # task_list = ['{"s_xuekeleibie": "自然科学总论", "url": "http://www.nssd.org/journal/cn/82217B/", "sha": "218edec6175ed9383728c4c1643d12d882d0123b"}']
            if task_list:
                for task in task_list:
                    try:
                        # 创建数据存储字典
                        save_data = {}
                        # json数据类型转换
                        task_data = json.loads(task)
                        sha = task_data['sha']
                        # 获取字段值存入字典并返回sha
                        self.handle(task_data=task_data, save_data=save_data)
                        # 保存数据到Hbase
                        if not save_data:
                            LOGGING.info('没有获取数据, 存储失败')
                            # 逻辑删除任务
                            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
                            LOGGING.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))
                            continue
                        if 'sha' not in save_data:
                            LOGGING.info('数据获取不完整, 存储失败')
                            # 逻辑删除任务
                            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
                            LOGGING.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))
                            continue
                        LOGGING.info('论文数据开始存储')
                        # 存储数据
                        success = self.dao.saveDataToHbase(data=save_data)

                        if success:
                            LOGGING.info('论文数据存储成功')
                            # 已完成任务
                            self.dao.finishTask(table=config.MYSQL_MAGAZINE, sha=sha)
                            # # 删除任务
                            # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                        else:
                            LOGGING.info('论文数据存储失败')
                            # 逻辑删除任务
                            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)

                        LOGGING.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))

                    except:
                        LOGGING.exception(str(traceback.format_exc()))
            else:
                time.sleep(1)
                continue

    def start(self):
        # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

        # # 创建gevent协程
        # g_list = []
        # for i in range(8):
        #     s = gevent.spawn(self.run)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        threadpool = ThreadPool(processes=config.THREAD_NUM)
        for i in range(config.THREAD_NUM):
            threadpool.apply_async(func=self.run)

        threadpool.close()
        threadpool.join()

def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    # process_start()

    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('====== Time consuming is %.2fs ======' %(end_time - begin_time))
