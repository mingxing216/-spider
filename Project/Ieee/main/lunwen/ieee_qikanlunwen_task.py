# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import traceback
import datetime
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Ieee.middleware import download_middleware
from Project.Ieee.service import service
from Project.Ieee.dao import dao
from Project.Ieee import config

log_file_dir = 'Ieee'  # LOG日志存放路径
LOGNAME = 'Ieee_期刊论文_task'  # LOG名
NAME = 'Ieee_期刊论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


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
        self.index_url = 'https://ieeexplore.ieee.org/rest/publication'
        self.cookie_dict = ''
        self.num = 0

    def __getResp(self, func, url, mode, data=None, cookies=None, referer=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies, referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None

    def get_catalog(self):
        # 访问期刊列表页，获取会议详情页及会议论文列表页
        payloadData = {
            'contentType': "periodicals",
            'publisher': None,
            'tabId': "topic"
        }

        jsonData = json.dumps(payloadData)

        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='POST',
                                    data=jsonData)
        if not index_resp:
            LOGGING.error('页面响应失败, url: {}'.format(self.index_url))
            return

        index_json = index_resp.json()

        # 获取期刊列表页首页的post请求punumber参数、起止时间
        journals = self.server.getQiKanProfile(content=index_json)
        # print(json.dumps(journals))
        # print(len(journals))
        # 期刊详情种子存入数据库，以及期刊论文列表种子进入队列
        for url in journals:
            # 存储期刊详情种子
            self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=url, ws='电气和电子工程师协会', es='期刊')
            # 期刊详情页接口url
            journal_url = 'https://ieeexplore.ieee.org/rest/publication/' + str(url['number']) + '/regular-issues'
            # 访问期刊详情页
            publish_resp = self.__getResp(func=self.download_middleware.getResp,
                                        url=journal_url,
                                        mode='GET')
            if not publish_resp:
                LOGGING.error('页面响应失败, url: {}'.format(journal_url))
                continue

            publish_json = publish_resp.json()

            # 获取期刊论文列表页post参数，url
            catalog_url = self.server.getCatalogUrl(content=publish_json, url=url)
            # print(catalog_url)
            # 队列期刊论文列表任务
            self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=catalog_url)

        # 判断列表页是否有下一页(总页数>1)
        journal_pages = self.server.totalPages(content=index_json)
        if journal_pages:
            for i in range(2, int(journal_pages) + 1):
                payloadData = {
                    'contentType': "periodicals",
                    'publisher': None,
                    'pageNumber': i,
                    'tabId': "topic"
                }

                jsonData = json.dumps(payloadData)

                next_resp = self.__getResp(func=self.download_middleware.getResp,
                                            url=self.index_url,
                                            mode='POST',
                                            data=jsonData)
                next_json = next_resp.json()
                # 获取期刊列表页首页的post请求punumber参数、起止时间
                journals = self.server.getQiKanProfile(content=next_json)
                # print(journals)
                # print(len(journals))
                # 会议种子存入数据库
                for url in journals:
                    self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=url, ws='电气和电子工程师协会', es='期刊')
                    # 期刊详情页接口url
                    journal_url = 'https://ieeexplore.ieee.org/rest/publication/' + str(url['number']) + '/regular-issues'
                    # 访问期刊详情页
                    publish_resp = self.__getResp(func=self.download_middleware.getResp,
                                                  url=journal_url,
                                                  mode='GET')
                    if not publish_resp:
                        LOGGING.error('页面响应失败, url: {}'.format(journal_url))
                        continue

                    publish_json = publish_resp.json()

                    # 获取期刊论文列表页post参数，url
                    catalog_url = self.server.getCatalogUrl(content=publish_json, url=url)
                    # print(catalog_url)
                    # 队列任务
                    self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=catalog_url)

            else:
                LOGGING.info('已翻到最后一页')
        else:
            LOGGING.info('已翻到最后一页')

    def run(self, catalog):
        # 数据类型转换
        catalog_dict = self.server.getEvalResponse(catalog)
        catalog_url = catalog_dict['url']
        qiKanUrl = catalog_dict['parenUrl']
        # 访问期刊论文列表页接口，获取响应
        payloadData = {
            'isnumber': catalog_dict['isnumber'],
            # 'pageNumber': 2,
            'punumber': catalog_dict['punumber'],
            'sortType': "vol-only-seq"
        }

        jsonData = json.dumps(payloadData)

        catalog_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=catalog_url,
                                    mode='POST',
                                    data=jsonData)
        if not catalog_resp:
            LOGGING.error('列表页首页响应获取失败, url: {}'.format(catalog_url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=catalog_dict)
            return

        catalog_json = catalog_resp.json()
        # print(json.dumps(catalog_json))

        # 获取期刊论文详情页，文档url及相关信息
        contents = self.server.getLunWenProfile(content=catalog_json, qikan=qiKanUrl)
        # print(json.dumps(contents))
        # print(len(contents))
        # 分别存储论文种子、文档种子进入mysql数据库
        for content in contents:
            # 获取论文详情种子及相关信息
            lunwen = {}
            lunwen['lunwenNumber'] = content['lunwenNumber']
            lunwen['url'] = content['lunwenUrl']
            lunwen['qiKanUrl'] = content['qiKanUrl']
            lunwen['pdfUrl'] = content['pdfUrl']
            # 存入mysql数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen, ws='电气和电子工程师协会', es='期刊论文')
            # 获取文档种子及相关信息
            if content['pdfUrl']:
                wendang = {}
                wendang['url'] = content['pdfUrl']
                wendang['parentUrl'] = content['lunwenUrl']
                wendang['title'] = content['title'].replace('"', '\\"').replace("'", "''")
                wendang['daXiao'] = content['daXiao']
                wendang['es'] = '期刊论文'
                # 存入mysql数据库
                self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=wendang, ws='电气和电子工程师协会', es='期刊论文')

        # 判断列表页是否有下一页(总页数>1)
        lunwen_pages = self.server.totalPages(content=catalog_json)
        if lunwen_pages:
            for i in range(2, int(lunwen_pages) + 1):
                payloadData = {
                    'isnumber': catalog_dict['isnumber'],
                    'pageNumber': i,
                    'punumber': catalog_dict['punumber'],
                    'sortType': "vol-only-seq"
                }

                jsonData = json.dumps(payloadData)

                catalog_resp = self.__getResp(func=self.download_middleware.getResp,
                                              url=catalog_url,
                                              mode='POST',
                                              data=jsonData)
                if not catalog_resp:
                    LOGGING.error('列表页第{}页响应失败, url: {}'.format(i, catalog_url))
                    # 队列一条任务
                    self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=catalog_dict)
                    return

                catalog_json = catalog_resp.json()

                # 获取期刊论文详情页，文档url及相关信息
                contents = self.server.getLunWenProfile(content=catalog_json, qikan=qiKanUrl)
                # print(json.dumps(contents))
                # print(len(contents))
                # 分别存储论文种子、文档种子进入mysql数据库
                for content in contents:
                    # 获取论文详情种子及相关信息
                    lunwen = {}
                    lunwen['lunwenNumber'] = content['lunwenNumber']
                    lunwen['url'] = content['lunwenUrl']
                    lunwen['qiKanUrl'] = content['qiKanUrl']
                    lunwen['pdfUrl'] = content['pdfUrl']
                    # 存入mysql数据库
                    self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen, ws='电气和电子工程师协会', es='期刊论文')
                    # 获取文档种子及相关信息
                    if content['pdfUrl']:
                        wendang = {}
                        wendang['url'] = content['pdfUrl']
                        wendang['parentUrl'] = content['lunwenUrl']
                        wendang['title'] = content['title'].replace('"', '\\"').replace("'", "''")
                        wendang['daXiao'] = content['daXiao']
                        wendang['es'] = '期刊论文'
                        # 存入mysql数据库
                        self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=wendang, ws='电气和电子工程师协会', es='期刊论文')

            else:
                LOGGING.info('已翻到最后一页')
        else:
            LOGGING.info('已翻到最后一页')

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_CATALOG,
                                         count=10,
                                         lockname=config.REDIS_CATALOG_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

def process_start():
    main = SpiderMain()
    try:
        main.get_catalog()
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()

    # po = Pool(4)
    # for i in range(4):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
