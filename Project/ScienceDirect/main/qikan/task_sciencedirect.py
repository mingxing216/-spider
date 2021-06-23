# -*- coding:utf-8 -*-
"""

"""
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
LOG_NAME = '英文期刊_task'  # LOG名
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

    def get_journal_profile(self):
            """
            获取期刊列表页中所有期刊种子, 存入mysql数据库, 同时存入redis队列
            """
            index_resp = self.download.get_resp(url=self.index_url, method='GET')
            if index_resp is None:
                logger.error('入口页响应失败, url: {}'.format(self.index_url))
                return

            if not index_resp['data']:
                logger.error('入口页响应失败, url: {}'.format(self.index_url))
                return

            index_text = index_resp['data'].text
            # with open ('index.html', 'w') as f:
            #     f.write(index_text)

            # 获取期刊列表总页数
            journal_pages = self.server.get_journal_total_page(text=index_text)
            # 期刊列表页翻页
            for page in range(1, int(journal_pages) + 1):
                url = self.catalog_url.format(page)
                # print(url)
                # 请求响应
                journal_resp = self.download.get_resp(url=url, method='GET')
                if journal_resp is None:
                    logger.error('downloader | 期刊列表第 {} 页响应失败, url: {}'.format(page, url))
                    return

                if not journal_resp['data']:
                    logger.error('downloader | 期刊列表第 {} 页响应失败, url: {}'.format(page, url))
                    return

                journal_text = journal_resp['data'].text
                # 获取期刊详情种子种子
                journal_list = self.server.get_journal_list(text=journal_text)
                # 存入mysql数据库
                for journal_url in journal_list:
                    # 保存url
                    self.num += 1
                    logger.info('number | 当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.sto_dao.save_task_to_mysql(table=config.MYSQL_MAGAZINE, memo=journal_url, ws='sciencedirect', es='期刊')

                # 期刊详情页进入队列
                self.spi_dao.queue_tasks_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=journal_list)

    def get_paper_catalog(self):
        self.timer.start()
        while True:
            # 获取任务
            category = self.spi_dao.get_one_task_from_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE)
            # category = '{"url": "http://103.247.176.188/Search.aspx?fd0=JI&kw0=%2246427%22&ob=dd", "journalUrl": "http://103.247.176.188/ViewJ.aspx?id=46427", "currentUrl": "http://103.247.176.188/Search.aspx?qx=&ob=dd&start=791260"}'
            if not category:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return

            else:
                # 数据类型转换
                task = json.loads(category)
                # 保存线程中的任务种子到临时队列
                self.spi_dao.queue_one_task_to_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)

                issue_catalog_url = task['url'] + '/issues'
                # 请求响应
                issue_catalog_resp = self.download.get_resp(url=issue_catalog_url, method='GET')
                if issue_catalog_resp is None:
                    # 删除临时队列中该种子
                    self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                    # 重新加载到队列
                    self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=task)
                    logger.error('downloader | 期列表页响应失败, url: {}'.format(issue_catalog_url))
                    return
                if not issue_catalog_resp['data']:
                    # 删除临时队列中该种子
                    self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                    # 重新加载到队列
                    self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=task)
                    logger.error('downloader | 期列表页响应失败, url: {}'.format(issue_catalog_url))
                    return
                issue_catalog_text = issue_catalog_resp['data'].text

                # 获取年列表页
                year_url_list = self.server.get_issues_catalog(issue_catalog_text)
                if year_url_list:
                    for year_info in year_url_list:
                        year_url = year_info[0]
                        year = str(year_info[1])
                        # 请求响应
                        paper_year_resp = self.download.get_resp(url=year_url, method='GET')
                        if paper_year_resp is None:
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                            # 重新加载到队列
                            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=task)
                            logger.error('downloader | 论文列表页响应失败, url: {}'.format(year_info))
                            return
                        if not paper_year_resp['data']:
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                            # 队列一条任务
                            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=task)
                            logger.error('downloader | 论文列表页响应失败, url: {}'.format(year_info))
                            return
                        try:
                            paper_year_json = paper_year_resp['data'].json()
                        except Exception:
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                            # 队列一条任务
                            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=task)
                            logger.info('downloader | 论文列表获取json数据失败')
                            return

                        paper_list = paper_year_json.get('data')
                        if not paper_list:
                            logger.info('journal | 期刊下无论文列表 | url: {}'.format(task['url']))
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)

                        else:
                            for paper_memo in paper_list:
                                paper_url = paper_memo.get('uriLookup')
                                if paper_url:
                                    url_list = paper_url.split('/')
                                    vol = url_list[2]
                                    issue = url_list[-1]
                                    # 参数
                                    journal_info = ['sciencedirect', '张明星']
                                    paper_memo['journalUrl'] = task['url']
                                    paper_memo['journalId'] = task['id']
                                    paper_memo['url'] = task['url'] + paper_url
                                    paper_memo['year'] = year
                                    paper_memo['vol'] = vol
                                    paper_memo['issue'] = issue
                                    journal_info.append(paper_memo['url'])
                                    journal_info.append(year)
                                    journal_info.append(vol)
                                    journal_info.append(issue)
                                    primary_key = 'sciencedirect_' + year + '_' + vol + '_' + issue
                                    journal_info.append(primary_key)

                                    # 期刊年卷期信息记录到数据库
                                    self.sto_dao.record_one_journal_info_to_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                                                  data_list=journal_info, key=primary_key)
                                    # 期刊论文列表页载入队列
                                    self.sto_dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_CATALOG, data=paper_memo)

                            else:
                                logger.info('journal | 期刊获取论文列表完毕 | url: {}'.format(task['url']))
                                # 删除临时队列中该种子
                                self.spi_dao.remove_one_task_from_redis(key=config.REDIS_MAGAZINE_TEMP, data=task)
                                # 已完成任务
                                self.spi_dao.finish_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=task['sha'])

def start():
    try:
        main = SpiderMain()
        # main.get_journal_profile()
        main.get_paper_catalog()
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
    threadpool = ThreadPool(processes=4)
    for j in range(4):
        threadpool.apply_async(func=start)

    threadpool.close()
    threadpool.join()


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    # process_start()
    po = Pool(processes=2)
    for i in range(2):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('======Time consuming is %.3f======' % (end_time - begin_time))
