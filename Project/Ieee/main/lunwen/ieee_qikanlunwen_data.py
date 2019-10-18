# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import copy
import traceback
import hashlib
from datetime import datetime
import requests
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Ieee.middleware import download_middleware
from Project.Ieee.service import service
from Project.Ieee.dao import dao
from Project.Ieee import config

log_file_dir = 'Ieee'  # LOG日志存放路径
LOGNAME = 'Ieee_期刊论文_data'  # LOG名
NAME = 'Ieee_期刊论文_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_LunWenServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.cookie_dict = ''

    def __getResp(self, func, url, mode, data=None, cookies=None):
        # while 1:
        # 发现验证码，最多访问页面10次
        for i in range(10):
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return None

    # 作者实体
    def zuoZhe(self, script, url, sha):
        try:
            authors = script['authors']
            for author in authors:
                # 图片url存储列表
                img_list = []

                author_dict = {}
                # 标题
                author_dict['title'] = self.server.getAuthorTitle(content=author)
                # 所在单位
                author_dict['suoZaiDanWei'] = self.server.getDanWei(content=author)
                # 正文
                author_dict['zhengWen'] = self.server.getZhengWen(content=author)
                # 标识
                author_dict['biaoShi'] = self.server.getBiaoShi(content=author)
                if author_dict['biaoShi']:
                    img_list.append(author_dict['biaoShi'])
                # 缩写_ORCID
                author_dict['ORCID'] = self.server.getORCID(content=author)
                # 获取sha
                id = url + '#' + author_dict['title'] + '#' + author_dict['suoZaiDanWei']
                sha1 = hashlib.sha1(id.encode('utf-8')).hexdigest()

                # 存储图片
                if img_list:
                    for img in img_list:
                        img_dict = {}
                        img_dict['bizTitle'] = author_dict['title']
                        img_dict['relEsse'] = self.server.guanLianRenWu(url=url, sha=sha1)
                        img_dict['relPics'] = {}
                        img_url = img
                        # # 存储图片种子
                        # self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
                        # 获取图片响应
                        media_resp = self.__getResp(func=self.download_middleware.getResp,
                                                    url=img_url,
                                                    mode='GET')
                        if not media_resp:
                            LOGGING.error('图片响应失败, url: {}'.format(img_url))
                            return '中断'

                        img_content = media_resp.content
                        # 存储图片
                        storage = self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')
                        if not storage:
                            # 逻辑删除任务
                            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                            LOGGING.error('图片数据存储失败, url: {}'.format(img_url))
                            continue

                # ======================== 公共字段
                # url
                author_dict['url'] = url
                # 生成key
                author_dict['key'] = url
                # 生成sha
                author_dict['sha'] = sha1
                # 生成ss ——实体
                author_dict['ss'] = '人物'
                # 生成es ——栏目名称
                author_dict['es'] = '期刊论文'
                # 生成ws ——目标网站
                author_dict['ws'] = '电气和电子工程师协会'
                # 生成clazz ——层级关系
                author_dict['clazz'] = '论文_期刊论文'
                # 生成biz ——项目
                author_dict['biz'] = '文献大数据'
                # 生成ref
                author_dict['ref'] = ''

                # 存储数据
                sto = self.dao.saveDataToHbase(data=author_dict)
                if not sto:
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                    LOGGING.error('作者数据存储失败, url: {}'.format(url))
        except Exception:
            pass

    # 论文实体
    def lunWen(self, save_data, script, number, url, sha):
        # 获取标题
        save_data['title'] = self.server.getField(script, 'title')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getField(script, 'abstract')
        # 获取期刊名称
        save_data['qiKanMingCheng'] = self.server.getField(script, 'publicationTitle')
        # 获取期号
        save_data['qiHao'] = self.server.getQiHao(script)
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getYeShu(script)
        # 获取在线出版日期
        riqi = self.server.getField(script, 'onlineDate')
        if riqi:
            try:
                save_data['zaiXianChuBanRiQi'] = str(datetime.strptime(riqi, "%d %B %Y"))
            except:
                save_data['zaiXianChuBanRiQi'] = riqi
        # 获取DOI
        save_data['DOI'] = self.server.getField(script, 'doi')
        # 获取ISBN Information
        save_data['ISBNInformation'] = self.server.getGuoJiField(script, 'isbn')
        # 获取ISSN Information
        save_data['ISSNInformation'] = self.server.getGuoJiField(script, 'issn')
        # 获取出版社
        save_data['chuBanShe'] = self.server.getField(script, 'publisher')
        # 获取赞助商
        save_data['zanZhuShang'] = self.server.getPeople(script, 'sponsors')
        # 获取基金
        save_data['jiJin'] = self.server.getJiJin(script)
        # 获取作者
        save_data['zuoZhe'] = self.server.getPeople(script, 'authors')
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(script)
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getPeople(script, 'pubTopics')
        # 获取时间
        save_data['shiJian'] = self.server.getShiJian(script)
        # 判断是否有参考文献
        references = self.server.hasWenXian(script, 'references')
        if references == 'true':
            # 获取参考文献url
            cankaoUrl = 'https://ieeexplore.ieee.org/rest/document/' + str(number) +'/references'
            # 获取页面响应
            cankao_resp = self.__getResp(func=self.download_middleware.getResp,
                                  url=cankaoUrl,
                                  mode='GET')
            if not cankao_resp:
                LOGGING.error('参考文献接口响应失败, url: {}'.format(cankaoUrl))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                return '中断'

            cankao_json = cankao_resp.json()
            # 获取参考文献
            save_data['canKaoWenXian'] = self.server.canKaoWenXian(content=cankao_json)
        else:
            save_data['canKaoWenXian'] = ""
        # 判断是否有引证文献
        citations = self.server.hasWenXian(script, 'citedby')
        if citations == 'true':
            # 获取参考文献url
            yinzhengUrl = 'https://ieeexplore.ieee.org/rest/document/' + str(number) +'/citations'
            # 获取页面响应
            yinzheng_resp = self.__getResp(func=self.download_middleware.getResp,
                                  url=yinzhengUrl,
                                  mode='GET')
            if not yinzheng_resp:
                LOGGING.error('引证文献接口响应失败, url: {}'.format(yinzhengUrl))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                return '中断'

            yinzheng_json = yinzheng_resp.json()
            # 获取引证文献
            save_data['yinZhengWenXian'] = self.server.yinZhengWenXian(content=yinzheng_json)
        else:
            save_data['yinZhengWenXian'] = ""
        # 关联作者
        save_data['guanLianZuoZhe'] = self.server.guanLianZuoZhe(script, url=url)
        # 获取作者实体字段值
        if save_data['guanLianZuoZhe']:
            return self.zuoZhe(script, url=url, sha=sha)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        qiKanUrl = task_data['qiKanUrl']
        pdfUrl = task_data['pdfUrl']
        number = task_data['lunwenNumber']

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        response = resp.text
        # with open('profile.html', 'w') as f:
        #     f.write(response)
        # return
        # print(response)
        # 获取script标签内容
        script = self.server.getScript(response)
        # print(script)

        result = self.lunWen(save_data=save_data, script=script, number=number, url=url, sha=sha)
        if result:
            return

        # ===================公共字段
        # 关联期刊
        save_data['guanLianQiKan'] = self.server.guanLianQiKan(url=qiKanUrl)
        # 关联文档
        save_data['guanLianWenDang'] = self.server.guanLianWenDang(url=pdfUrl)
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成es ——栏目名称
        save_data['es'] = '期刊论文'
        # 生成ws ——目标网站
        save_data['ws'] = '电气和电子工程师协会'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 返回sha为删除任务做准备
        return sha

    def run(self, task):
        # 创建数据存储字典
        save_data = {}

        # 获取字段值存入字典并返回sha
        sha = self.handle(task=task, save_data=save_data)

        # 保存数据到Hbase
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        # 存储数据
        success = self.dao.saveDataToHbase(data=save_data)
        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_QIKAN_PAPER, count=10, lockname=config.REDIS_QIKAN_PAPER_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))
            # print(task_list)

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for task in task_list:
                #     threadpool.apply_async(func=self.run, args=(task,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)
            else:
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"lunwenNumber": "6792108", "url": "https://ieeexplore.ieee.org/document/6792108/", "qiKanUrl": "https://ieeexplore.ieee.org/xpl/aboutJournal.jsp?punumber=7", "pdfUrl": "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8106676"}')
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()

    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
