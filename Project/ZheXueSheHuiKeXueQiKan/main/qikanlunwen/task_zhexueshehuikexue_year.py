# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import json
import requests
import time
import traceback
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from Project.ZheXueSheHuiKeXueQiKan.main.qikanlunwen import data_zhexueshehuikexue

log_file_dir = 'SheHuiKeXue'  # LOG日志存放路径
LOGNAME = '<国家哲学社会科学_年列表_task>'  # LOG名
NAME = '国家哲学社会科学_年列表_task'  # 爬虫名
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
        # 入口页url
        self.index_url = 'http://www.nssd.org/journal/fund.aspx'
        self.total_url = 'http://www.nssd.org/journal/record.aspx'
        self.s = None
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def run(self):
        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE,
                                             count=1,
                                             lockname=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE_LOCK)
            # print(category_list)
            if category_list:
                for category in category_list:
                    # 数据类型转换
                    task = json.loads(category)
                    # print(task)
                    qikan_url = task['url']
                    xuekeleibie = task['s_xuekeleibie']
                    # 获取期刊详情页
                    category_resp = self.__getResp(url=qikan_url, method='GET')
                    if not category_resp:
                        LOGGING.error('期刊详情页响应失败, url: {}'.format(qikan_url))
                        # 队列一条任务
                        self.dao.QueueOneTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE, data=task)
                        break
                    # 获取期刊年列表
                    year_list = self.server.getYears(text=category_resp.text, xuekeleibie=xuekeleibie, qikanUrl=qikan_url)
                    # print(year_list)
                    # 存储年列表到mysql数据库
                    for year in year_list:
                        self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=year, ws='国家哲学社会科学', es='期刊年列表')
                        LOGGING.info('当前已存年列表种子数量: {}'.format(self.num + 1))

                    else:
                        LOGGING.info('{}类下所有年期刊列表种子获取完毕'.format(xuekeleibie))
                        # 标记已完成期刊任务
                        self.dao.finishTask(table=config.MYSQL_MAGAZINE, sha=task['sha'])

            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

    def start(self):
        # # 创建gevent协程
        # g_list = []
        # for category in category_list:
        #     s = gevent.spawn(self.run, category)
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
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    # process_start()
    # 创建多进程
    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' %(end_time - begin_time))
