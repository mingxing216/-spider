# -*- coding:utf-8 -*-

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
from multiprocessing.pool import Pool, ThreadPool

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Utils import timers
from Project.EnSheHuiKeXue.service.service import CaptchaProcessor
from Project.EnSheHuiKeXue.middleware import download_middleware
from Project.EnSheHuiKeXue.service import service
from Project.EnSheHuiKeXue.dao import dao
from Project.EnSheHuiKeXue import config

LOG_FILE_DIR = 'EnSheHuiKeXue'  # LOG日志存放路径
LOG_NAME = '英文期刊_task'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_type=config.PROXY_TYPE,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT,
                                                       proxy_country=config.COUNTRY,
                                                       proxy_city=config.CITY)
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
        self.index_url = 'http://103.247.176.188/Journal.aspx'
        # 获取下一层分类url
        self.child_url = 'http://103.247.176.188/Childnode.aspx'
        self.num = 0

    def get_journal_profile(self):
            """
            获取期刊列表页中所有期刊种子，存入mysql数据库；同时获取论文列表页，存入redis队列
            """
            index_resp = self.download.get_resp(url=self.index_url, method='GET')
            if not index_resp:
                logger.error('入口页面响应失败, url: {}'.format(self.index_url))
                return

            # with open ('index.html', 'w') as f:
            #     f.write(index_text)

            index_text = index_resp.text
            # 获取期刊列表总页数
            journal_pages = self.server.get_journal_total_page(text=index_text)
            # print(journal_pages)
            # 期刊列表页翻页
            for page in range(1, int(journal_pages) + 1):
                url = self.index_url + '?Page={}'.format(page)
                # 请求响应
                journal_resp = self.download.get_resp(url=url, method='GET')
                if not journal_resp:
                    logger.error('downloader | 期刊列表第 {} 页响应失败, url: {}'.format(page, url))
                    return
                journal_text = journal_resp.text
                # 获取期刊详情种子、论文列表页种子
                journal_list, paper_list = self.server.get_journal_list(text=journal_text)
                # 存入mysql数据库
                for journal_url in journal_list:
                    # 保存url
                    self.num += 1
                    logger.info('number | 当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.dao.save_task_to_mysql(table=config.MYSQL_MAGAZINE, memo=journal_url, ws='英文哲学社会科学', es='期刊')

                # 论文列表页进入队列
                self.dao.queue_tasks_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=paper_list)

    def get_page_count(self, first_url, task):
        """获取论文列表页总页数"""
        paper_resp = self.captcha_processor.process_first_request(url=first_url, method='GET', s=self.s)
        if not paper_resp:
            logger.error('downloader | 论文第 1 页列表页响应失败, url: {}'.format(first_url))
            # 队列一条任务
            self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
            return
        # 处理验证码
        paper_resp = self.captcha_processor.process(paper_resp)
        if paper_resp is None:
            # 队列一条任务
            self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
            return

        # 获取论文列表总页数
        page_counts = self.server.get_paper_total_page(text=paper_resp.text)

        return page_counts

    @staticmethod
    def get_all_pages(start_page, end_page):
        """获取论文列表页所有url"""
        all_pages = []
        for count in range(start_page, end_page + 1):
            page = 'http://103.247.176.188/Search.aspx?qx=&ob=dd&start={}'.format((count - 1) * 10)
            all_pages.append(page)

        return all_pages

    def get_profile(self, url_list):
        """论文详情种子存入mysql数据库"""
        for paper_url in url_list:
            # 保存url
            self.num += 1
            logger.info('number | 当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=paper_url, ws='英文哲学社会科学', es='期刊论文')

    def get_current_catalog(self, first_url, journal_url, current_url, task):
        """论文列表当前页翻页"""
        # 获取列表总页数
        end_page = self.get_page_count(first_url, task)

        try:
            start_page = int(int(re.findall(r"\d+$", current_url)[0])/10 + 1)
        except Exception:
            start_page = 1

        all_pages = self.get_all_pages(start_page, end_page)

        next_num = start_page
        for page_url in all_pages:
            # 请求论文列表页
            next_resp = self.captcha_processor.process_first_request(url=page_url, method='GET', s=self.s)
            if not next_resp:
                logger.error('downloader | 论文第 {} 页列表页响应失败, url: {}'.format(next_num, page_url))
                # 队列一条任务
                task['currentUrl'] = page_url
                self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                return
            # 处理验证码
            next_resp = self.captcha_processor.process(next_resp)
            if next_resp is None:
                # 队列一条任务
                task['currentUrl'] = page_url
                self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                return
            next_text = next_resp.text
            # 响应成功，添加log日志
            logger.info('downloader | 已翻到第{}页'.format(next_num))
            # 获取论文详情种子、全文种子
            paper_url_list = self.server.get_paper_list(next_text, journal_url)
            # 详情种子存储
            if paper_url_list:
                self.get_profile(paper_url_list)

            # 翻页计数
            next_num += 1

        else:
            logger.info('downloader | 已翻到最后一页')
            return

    def get_paper_catalog(self, catalog_url, journal_url, task):
        """论文列表页翻页"""
        # 获取列表总页数
        end_page = self.get_page_count(catalog_url, task)
        if end_page is None:
            return

        start_page = 1

        all_pages = self.get_all_pages(start_page, end_page)

        next_num = start_page
        for page_url in all_pages:
            # 请求论文列表页
            next_resp = self.captcha_processor.process_first_request(url=page_url, method='GET', s=self.s)
            if not next_resp:
                logger.error('downloader | 论文第 {} 页列表页响应失败, url: {}'.format(next_num, page_url))
                # 队列一条任务
                task['currentUrl'] = page_url
                self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                return
            # 处理验证码
            next_resp = self.captcha_processor.process(next_resp)
            if next_resp is None:
                # 队列一条任务
                task['currentUrl'] = page_url
                self.dao.queue_one_task_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                return
            next_text = next_resp.text
            # 响应成功，添加log日志
            logger.info('downloader | 已翻到第{}页'.format(next_num))
            # 获取论文详情种子、全文种子
            paper_url_list = self.server.get_paper_list(next_text, journal_url)
            # 详情种子存储
            if paper_url_list:
                self.get_profile(paper_url_list)

            # 翻页计数
            next_num += 1

        else:
            logger.info('downloader | 已翻到最后一页')
            return

    def run(self):
        self.timer.start()
        while 1:
            # 获取任务
            category = self.dao.get_one_task_from_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG)
            # category = '{"url": "http://103.247.176.188/Search.aspx?fd0=JI&kw0=%2267338%22&ob=dd", "journalUrl": "http://103.247.176.188/ViewJ.aspx?id=67338", "totalPage": "634", "currentUrl": "http://103.247.176.188/Search.aspx?qx=&ob=dd&start=300"}'
            # print(category)
            if category:
                # 数据类型转换
                task = json.loads(category)
                # print(task)
                paper_catalog_url = task['url']
                journal_url = task['journalUrl']
                current_url = task.get('currentUrl')
                if current_url:
                    # 从当前页开始翻页，获取并存储详情种子
                    self.get_current_catalog(paper_catalog_url, journal_url, current_url, task)
                else:
                    # 列表页翻页，获取并存储详情种子
                    self.get_paper_catalog(paper_catalog_url, journal_url, task)

            else:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return


def start():
    main = SpiderMain()
    try:
        # main.get_journal_profile()
        # main.paper_total_page()
        main.run()
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
