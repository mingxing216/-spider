# -*-coding:utf-8-*-

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
from Project.ScienceDirect.service.service import CaptchaProcessor
from Project.ScienceDirect.middleware import download_middleware
from Project.ScienceDirect.service import service
from Project.ScienceDirect.dao import dao
from Project.ScienceDirect import config

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
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)
        self.s = requests.Session()
        self.captcha_processor = CaptchaProcessor(self.server, self.download, self.s, logger)


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
            if not index_resp:
                logger.error('入口页响应失败, url: {}'.format(self.index_url))
                return

            # with open ('index.html', 'w') as f:
            #     f.write(index_resp.text)

            index_text = index_resp.text
            # 获取期刊列表总页数
            journal_pages = self.server.get_journal_total_page(text=index_text)
            # print(journal_pages)
            # 期刊列表页翻页
            for page in range(1, int(journal_pages) + 1):
                url = self.catalog_url.format(page)
                # 请求响应
                journal_resp = self.download.get_resp(url=url, method='GET')
                if not journal_resp:
                    logger.error('downloader | 期刊列表第 {} 页响应失败, url: {}'.format(page, url))
                    return
                journal_text = journal_resp.text
                # 获取期刊详情种子种子
                journal_list = self.server.get_journal_list(text=journal_text)
                # 存入mysql数据库
                for journal_url in journal_list:
                    # 保存url
                    self.num += 1
                    logger.info('number | 当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.dao.save_task_to_mysql(table=config.MYSQL_MAGAZINE, memo=journal_url, ws='sciencedirect', es='期刊')

                # 期刊详情页进入队列
                self.dao.queue_tasks_to_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE, data=journal_list)

    def get_paper_catalog(self):
        self.timer.start()
        while 1:
            # 获取任务
            category = self.dao.get_one_task_from_redis(key=config.REDIS_SCIENCEDIRECT_MAGAZINE)
            # category = '{"url": "http://103.247.176.188/Search.aspx?fd0=JI&kw0=%2246427%22&ob=dd", "journalUrl": "http://103.247.176.188/ViewJ.aspx?id=46427", "currentUrl": "http://103.247.176.188/Search.aspx?qx=&ob=dd&start=791260"}'
            if category:
                # 数据类型转换
                task = json.loads(category)
                print(task)
                issue_catalog_url = task['url'] + '/issues'
                # 请求响应
                issue_catalog_resp = self.download.get_resp(url=issue_catalog_url, method='GET')
                if not issue_catalog_resp:
                    logger.error('downloader | 期列表页响应失败, url: {}'.format(issue_catalog_url))
                    return
                issue_catalog_text = issue_catalog_resp.text

                # 获取期列表页
                issues_url_list = self.server.get_issues_catalog(issue_catalog_text)
                if issues_url_list:
                    for issue_url in issues_url_list:
                        # 请求响应
                        paper_catalog_resp = self.download.get_resp(url=issue_url, method='GET')
                        if not paper_catalog_resp:
                            logger.error('downloader | 论文列表页响应失败, url: {}'.format(issue_url))
                            return
                        try:
                            paper_catalog_json = paper_catalog_resp.json()
                        except Exception:
                            logger.info('downloader | 论文列表获取json数据失败')
                            return

                        paper_list = paper_catalog_json.get('data')
                        if paper_list:
                            for paper_memo in paper_list:
                                paper_url = paper_memo.get('uriLookup')
                                if paper_url:
                                    paper_memo['url'] = task['url'] + paper_url
                                    # 存入数据库
                                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=paper_memo,
                                                                ws='sciencedirect', es='期刊论文catalog')
                                    # 期刊论文列表页载入队列
                                    self.dao.queue_one_task_to_redis(key=config.REDIS_SCIENCEDIRECT_CATALOG, data=paper_memo)

            else:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return


def start():
    main = SpiderMain()
    try:
        # main.get_journal_profile()
        main.get_paper_catalog()
        # main.run()
    except Exception:
        logger.error(str(traceback.format_exc()))

    print(main.captcha_processor.recognize_code.show_report())


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
