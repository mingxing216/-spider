# -*-coding:utf-8-*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import hashlib
import sys
import os
import json
import requests
import time
import traceback
import re
from multiprocessing.pool import Pool, ThreadPool

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Utils import timers
from Project.ScienceDirect.middleware import download_middleware
from Project.ScienceDirect.service import service
from Project.ScienceDirect.dao import dao
from Project.ScienceDirect import config
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME, STO_HOST, STO_PORT, STO_USER, STO_PASS, STO_NAME

LOG_FILE_DIR = 'ScienceDirect'  # LOG日志存放路径
LOG_NAME = '英文期刊论文_task'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.Server(logging=logger)
        self.spi_dao = dao.Dao(logging=logger,
                               host=SPI_HOST, port=SPI_PORT, user=SPI_USER, pwd=SPI_PASS, db=SPI_NAME,
                               mysqlpool_number=config.MYSQL_POOL_NUMBER,
                               redispool_number=config.REDIS_POOL_NUMBER)
        self.sto_dao = dao.Dao(logging=logger,
                               host=STO_HOST, port=STO_PORT, user=STO_USER, pwd=STO_PASS, db=STO_NAME,
                               mysqlpool_number=config.MYSQL_POOL_NUMBER,
                               redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        self.timer = timers.Timer()
        # 入口页url
        self.index_url = 'https://www.sciencedirect.com/browse/journals-and-books?contentType=JL'
        # 期刊列表页接口
        self.catalog_url = 'https://www.sciencedirect.com/browse/journals-and-books?page={}&contentType=JL'
        # 计数
        self.num = 0

    def get_profile(self, url_list, task):
        """论文详情种子存入mysql数据库"""
        for paper_url in url_list:
            # 保存url
            self.num += 1
            logger.info('number | 当前已抓种子数量: {}'.format(self.num))
            paper_sha = hashlib.sha1(paper_url.get('url').encode('utf-8')).hexdigest()
            mysql_paper = 'job_paper_{}'.format(paper_sha[0])
            # 存入数据库
            self.sto_dao.save_task_to_mysql(table=mysql_paper, memo=paper_url, ws='sciencedirect', es='期刊论文')

        # 更新mysql期刊信息表中年期状态
        year = task.get('year')
        vol = task.get('vol')
        issue = task.get('issue')
        self.sto_dao.update_journal_info_to_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                  ws='sciencedirect',
                                                  journal_id=vol,
                                                  year=year,
                                                  issue=issue)

    def get_paper_catalog(self, task):
        """论文列表页翻页"""
        catalog_url = task['url']
        # 请求响应
        paper_catalog_resp = self.download.get_resp(url=catalog_url, method='GET')
        if paper_catalog_resp is None:
            # 删除临时队列中该种子
            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_PAPER_TEMP, data=task)
            # 重新加载到队列
            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_CATALOG, data=task)
            logger.error('downloader | 论文列表页响应失败, url: {}'.format(catalog_url))
            return
        if not paper_catalog_resp['data']:
            # 删除临时队列中该种子
            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_PAPER_TEMP, data=task)
            # 重新加载到队列
            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_CATALOG, data=task)
            logger.error('downloader | 论文列表页响应失败, url: {}'.format(catalog_url))
            return
        paper_catalog_text = paper_catalog_resp['data'].text
        # with open ('catalog.html', 'w') as f:
        #     f.write(paper_catalog_text)

        # 获取论文详情种子、全文种子、类型、权限等
        paper_url_list = self.server.get_paper_list(paper_catalog_text, task)
        # 详情种子存储
        if paper_url_list:
            self.get_profile(paper_url_list, task)

    def run(self):
        self.timer.start()
        while 1:
            # 获取任务
            category = self.spi_dao.get_one_task_from_redis(key=config.REDIS_SCIENCEDIRECT_CATALOG)
            # category = '{"url": "http://103.247.176.188/Search.aspx?fd0=JI&kw0=%2246427%22&ob=dd", "journalUrl": "http://103.247.176.188/ViewJ.aspx?id=46427", "currentUrl": "http://103.247.176.188/Search.aspx?qx=&ob=dd&start=780200"}'
            if not category:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return

            else:
                # 数据类型转换
                task = json.loads(category)
                # print(task)
                # 保存线程中的任务种子到临时队列
                self.spi_dao.queue_one_task_to_redis(key=config.REDIS_PAPER_TEMP, data=task)
                # 列表页翻页，获取并存储详情种子
                self.get_paper_catalog(task)


def start():
    try:
        main = SpiderMain()
        # main.get_journal_profile()
        # main.paper_catalog_page()
        main.run()
    except Exception:
        logger.error(str(traceback.format_exc()))


def process_start():
    # # 创建gevent协程
    # g_list = []
    # for category in category_list:
    #     s = gevent.spawn(self.run, category)
    #     g_list.append(s)
    # gevent.joinall(g_list)

    # self.run()

    # 创建线程池
    threadpool = ThreadPool(processes=1)
    for j in range(1):
        threadpool.apply_async(func=start)

    threadpool.close()
    threadpool.join()


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    # process_start()
    po = Pool(processes=1)
    for i in range(1):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('======Time consuming is %.3f======' % (end_time - begin_time))
