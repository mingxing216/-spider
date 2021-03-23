# -*- coding:utf-8 -*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import re
import json
import random
import hashlib
import traceback
from multiprocessing.pool import Pool, ThreadPool

import requests

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Utils import timeutils, timers
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY, LANG_API

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_QiKan(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        self.timer = timers.Timer()
        self.lang_api = LANG_API
        self.s = requests.Session()

    def _get_resp(self, url, method, s=None, data=None, host=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download.get_resp(s=s, url=url, method=method, data=data, host=host,
                                          cookies=cookies, referer=referer)
            if resp:
                if resp['status'] == 200:
                    if '请输入验证码' in resp['data'].text or len(resp['data'].text) < 10:
                        logger.error('captcha | 出现验证码: {}'.format(url))
                        continue
            return resp
        else:
            return

    def img(self, img_dict):
        # 获取图片响应
        media_resp = self._get_resp(url=img_dict['url'], method='GET', host='c61.cnki.net')
        if media_resp['status'] == 404:
            return True

        if not media_resp['data']:
            logger.error('downloader | 图片响应失败, url: {}'.format(img_dict['url']))
            return

        img_content = media_resp['data'].content
        # 存储图片
        content_type = 'image/jpeg'
        suc = self.dao.save_media_to_hbase(media_url=img_dict['url'], content=img_content, item=img_dict,
                                           type='image', contype=content_type)
        if suc:
            return True
        else:
            return

    def handle(self, task_data, save_data):
        # 获取task数据
        # print(task_data)
        url = task_data['url']
        try:
            _id = re.findall(r"pykm=(\w+)$", url)[0]
        except Exception:
            return

        key = '中国知网|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()
        # 获取cookie
        self._get_resp(url='https://navi.cnki.net/KNavi/Journal.html', method='GET', s=self.s)
        # 获取期刊详情页源码
        resp = self._get_resp(url=url, method='GET', s=self.s, host='navi.cnki.net')
        if resp['status'] == 404:
            return
        # with open('article.html', 'w', encoding='utf-8') as f:
        #     f.write(resp.text)

        if not resp['data']:
            logger.error('downloader | 页面响应失败, url: {}'.format(url))
            return

        response = resp['data'].text
        # ========================获取数据==========================
        # 标题
        save_data['title'] = self.server.get_title(response)
        if not save_data['title']:
            return

        # # 获取核心收录
        # save_data['heXinShouLu'] = self.server.get_he_xin_shou_lu(response)
        # 获取外文名称
        save_data['parallel_title'] = {}
        t_text = self.server.get_parallel_title(response)
        if t_text:
            save_data['parallel_title']['text'] = t_text
            form_data = {'q': t_text}
            try:
                lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5, 10))
                lang = lang_resp.json().get('responseData').get('language')
            except:
                return
            save_data['parallel_title']['lang'] = lang
        # 获取图片
        save_data['cover'] = self.server.get_cover(response)
        # 获取曾用名
        save_data['former_name'] = self.server.get_data(response, '曾用刊名')
        # 获取主办单位
        save_data['responsible_organization'] = self.server.get_more_data(response, '主办单位')
        # 获取出版周期
        save_data['period'] = self.server.get_data(response, '出版周期')
        # 获取issn
        save_data['issn'] = self.server.get_data(response, 'ISSN')
        # 获取CN
        save_data['cn'] = self.server.get_data(response, 'CN')
        # 获取出版地
        save_data['place_of_publication'] = self.server.get_data(response, '出版地')
        # 获取语种
        save_data['language'] = self.server.get_data(response, '语种')
        # 获取开本
        save_data['book_size'] = self.server.get_data(response, '开本')
        # 获取邮发代号
        save_data['issuing_code'] = self.server.get_data(response, '邮发代号')
        # 获取创刊时间
        shijian = self.server.get_data(response, '创刊时间')
        save_data['start_year_of_publication'] = timeutils.get_date_time_record(shijian)
        # 获取出版文献量
        save_data['number_of_published_articles'] = self.server.get_counts(response, '出版文献量')
        # 获取总下载次数
        save_data['journal_downloads'] = self.server.get_counts(response, '总下载次数')
        # 获取总被引次数
        save_data['journal_cites'] = self.server.get_counts(response, '总被引次数')
        # 获取影响因子（复合影响因子、综合影响因子）
        save_data['impact_factor'] = self.server.get_impact_factor(response)
        # 获取来源数据库
        save_data['databases'] = self.server.get_databases(response)
        # 获取中文核心期刊来源版本
        save_data['in_chinese_core_journals'] = self.server.get_chinese_core_journals(response)
        # 获取期刊荣誉
        save_data['journal_honors'] = self.server.get_journal_honors(response)
        # 学科类别
        save_data['subject_classification_name'] = task_data.get('s_xueKeLeiBie', '')
        # 核心期刊导航
        save_data['classification_name'] = task_data.get('s_zhongWenHeXinQiKanMuLu', '')

        # 保存图片
        if save_data['cover']:
            img_dict = dict()
            img_dict['url'] = save_data['cover']
            img_dict['bizTitle'] = save_data['title']
            img_dict['relEsse'] = self.server.rela_journal(url, key, sha)
            img_dict['relPics'] = {}

            # 存储图片
            suc = self.img(img_dict=img_dict)
            if not suc:
                return

        # =========================== 公共字段
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
        save_data['ws'] = '中国知网'
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
        save_data['metadata_version'] = 'V1.2'
        # 采集脚本版本号
        save_data['script_version'] = 'V1.3'

    def run(self):
        task_timer = timers.Timer()
        logger.info('thread | start')
        # 第一次请求的等待时间
        self.timer.start()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.info('thread | wait download delay time | use time: {}'.format(self.timer.use_time()))
        # 单线程无限循环
        while True:
            # 获取任务
            logger.info('task start')
            task_timer.start()
            task = self.dao.get_one_task_from_redis(key=config.REDIS_QIKAN_MAGAZINE)
            # task = '{"url": "https://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=WBXB", "s_xueKeLeiBie": "信息科技_无线电电子学", "s_zhongWenHeXinQiKanMuLu": "第七编 工业技术_无线电电子学、电信技术", "sha": "30a13f1189561739bd2493feb5c10c455e5c70bf"}'
            if task:
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
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | No data.'.format(task_timer.use_time()))
                        continue
                    if 'sha' not in save_data:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | Data Incomplete.'.format(task_timer.use_time()))
                        continue
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=save_data, ss_type=save_data['ss'], sha=save_data['sha'], url=save_data['url'])

                    if success:
                        # 已完成任务
                        self.dao.finish_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        # # 删除任务
                        # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                    else:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)

                    logger.info(
                        'task end | task success | use time: {}'.format(task_timer.use_time()))

                except:
                    logger.exception(str(traceback.format_exc()))
                    logger.error('task end | task failed | use time: {}'.format(task_timer.use_time()))
            else:
                time.sleep(1)
                continue


def start():
    main = SpiderMain()
    try:
        main.run()
    except:
        logger.exception(str(traceback.format_exc()))


def process_start():
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
    for j in range(config.THREAD_NUM):
        threadpool.apply_async(func=start)

    threadpool.close()
    threadpool.join()


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
