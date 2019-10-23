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
from Project.Nasa.middleware import download_middleware
from Project.Nasa.service import service
from Project.Nasa.dao import dao
from Project.Nasa import config

log_file_dir = 'Nasa'  # LOG日志存放路径
LOGNAME = 'Nasa_会议论文_task'  # LOG名
NAME = 'Nasa_会议论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.LunWen_LunWenServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.index_url = 'https://ntrs.nasa.gov/advSearch.jsp'
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
        # 访问入口页，获取论文列表页参数
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('页面响应失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text

        selector = self.server.getSelector(resp=index_text)
        # return
        # 获取论文列表页参数，及对应列表页所在栏目
        papers = self.server.getPaperPara(selector=selector)
        print(papers)
        # print(papers)
        if papers:
            # 队列任务
            self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=papers)

    def run(self, catalog):
        # 数据类型转换
        catalog_dict = self.server.getEvalResponse(catalog)
        catalog_url = catalog_dict['url']
        es = catalog_dict['es']
        catalog_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=catalog_url,
                                    mode='GET')
        if not catalog_resp:
            LOGGING.error('列表页首页响应获取失败, url: {}'.format(catalog_url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=catalog_dict)
            return

        catalog_text = catalog_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(catalog_text)
        selector = self.server.getSelector(resp=catalog_text)

        # 获取论文详情页，文档url及相关信息
        contents = self.server.getLunWenProfile(selector=selector, es=es)
        # print(contents)
        print(len(contents))
        # 分别存储论文种子、文档种子进入mysql数据库
        for content in contents:
            # 获取论文详情种子及相关信息
            lunwen = {}
            lunwen['url'] = content['lunwenUrl']
            lunwen['pdfUrl'] = content['pdfUrl']
            lunwen['es'] = content['es']
            # 存入mysql数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen, ws='美国宇航局', es=lunwen['es'])
            # 获取文档种子及相关信息
            if content['pdfUrl']:
                wendang = {}
                wendang['url'] = content['pdfUrl']
                wendang['parentUrl'] = content['lunwenUrl']
                wendang['title'] = content['title'].replace('"', '\\"').replace("'", "''")
                wendang['daXiao'] = content['pdfSize']
                wendang['es'] = content['es']
                # 存入mysql数据库
                self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=wendang, ws='美国宇航局', es=wendang['es'])

        # 判断列表页是否有下一页
        next_page = self.server.nextPages(selector=selector)
        # 翻页
        num = 2

        while True:
            # 如果有，请求下一页，获得响应
            if next_page:
                next_url = next_page

                next_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=next_url,
                                           mode='GET')

                # 如果响应获取失败，重新访问，并记录这一页种子
                if not next_resp:
                    LOGGING.error('第{}页响应获取失败, url: {}'.format(num, next_url))
                    # 队列一条任务
                    catalog_dict['url'] = next_url
                    self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=catalog_dict)
                    continue
                # 响应成功，添加log日志
                LOGGING.info('已翻到第{}页'.format(num))

                num += 1

                # 获得响应成功，提取详情页种子
                next_text = next_resp.text
                select = self.server.getSelector(resp=next_text)

                # 获取论文详情页，文档url及相关信息
                next_contents = self.server.getLunWenProfile(selector=select, es=es)
                # print(next_contents)
                print(len(next_contents))
                # 分别存储论文种子、文档种子进入mysql数据库
                for content in next_contents:
                    # 获取论文详情种子及相关信息
                    lunwen = {}
                    lunwen['url'] = content['lunwenUrl']
                    lunwen['pdfUrl'] = content['pdfUrl']
                    lunwen['es'] = content['es']
                    # 存入mysql数据库
                    self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen, ws='美国宇航局', es=lunwen['es'])
                    # 获取文档种子及相关信息
                    if content['pdfUrl']:
                        wendang = {}
                        wendang['url'] = content['pdfUrl']
                        wendang['parentUrl'] = content['lunwenUrl']
                        wendang['title'] = content['title'].replace('"', '\\"').replace("'", "''")
                        wendang['daXiao'] = content['pdfSize']
                        wendang['es'] = content['es']
                        # 存入mysql数据库
                        self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=wendang, ws='美国宇航局', es=wendang['es'])

                # 判断是否有下一页
                next_page = self.server.nextPages(selector=select)

            else:
                LOGGING.info('已翻到最后一页')
                break

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_CATALOG,
                                         count=2,
                                         lockname=config.REDIS_CATALOG_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))
            print(task_list)

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
