# -*-coding:utf-8-*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import json
import requests
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Utils import timers
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊论文_task'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_LunWen(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化期刊时间列表种子模板
        self.timer = timers.Timer()
        self.qiKan_time_url_template = 'https://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunwen_url_template = 'https://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'
        # 会话
        self.s = requests.Session()
        # 记录存储种子数量
        self.num = 0

    def _get_resp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download.get_resp(s=s, url=url, method=method, data=data,
                                          cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    logger.error('captcha | 出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def run(self):
        self.timer.start()
        while 1:
            # 获取任务
            category = self.dao.get_one_task_from_redis(key=config.REDIS_QIKAN_CATALOG)
            # category = '{"url": "https://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=SKTC", "s_xueKeLeiBie": "工程科技II_航空航天科学与工程", "s_zhongWenHeXinQiKanMuLu": "", "sha": "a4df9ea37b93729c368995f9dc30cc1885b13196"}'
            # print(category)
            if category:
                # 数据类型转换
                task = json.loads(category)
                # print(task)
                qiKanUrl = task.get('url')
                xueKeLeiBie = task.get('s_xueKeLeiBie')

                # # 创建cookies
                # cookies = self.download_middleware.create_cookie(url=qiKanUrl)
                # if not cookies:
                #     # 队列一条任务
                #     self.dao.QueueOneTask(key=config.REDIS_QIKAN_CATALOG, data=task)
                #     return
                # # 设置会话cookies
                # self.s.cookies = cookies

                # 生成单个知网期刊的时间列表种子
                qikan_time_list_url, pcode, pykm = self.server.qikan_time_list_url(qiKanUrl, self.qiKan_time_url_template)
                # print(qikan_time_list_url, pcode, pykm)
                # 获取期刊时间列表页html源码
                if qikan_time_list_url:
                    qikanTimeListHtml = self._get_resp(url=qikan_time_list_url, method='GET')
                    if not qikanTimeListHtml:
                        logger.error('catalog | 期刊时间列表页获取失败, url: {}'.format(qikan_time_list_url))
                        # 队列一条任务
                        self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                        return

                    # 获取期刊【年】、【期】列表
                    # 循环获取指定年、期页文章列表页种子
                    for qikan_year in self.server.get_qikan_time_list(qikanTimeListHtml):
                        # 获取文章列表页种子
                        article_url = self.server.get_article_list_url(url=self.lunwen_url_template,
                                                                       data=qikan_year,
                                                                       pcode=pcode,
                                                                       pykm=pykm)
                        # print(article_url)
                        # 获取论文列表页html源码
                        if article_url:
                            article_list_html = self._get_resp(url=article_url, method='GET')
                            if not article_list_html:
                                logger.error('catalog | 论文列表页html源码获取失败, url: {}'.format(article_url))
                                # 队列一条任务
                                self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                return

                            # 获取论文详情种子列表
                            article_url_list = self.server.get_article_url_list(article_list_html, qiKanUrl, xueKeLeiBie, qikan_year)
                            if article_url_list:
                                for paper_url in article_url_list:
                                    # print(paper_url)
                                    # 存储种子
                                    self.num += 1
                                    logger.info('profile | 已抓种子数量: {}'.format(self.num))
                                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=paper_url, ws='中国知网', es='期刊论文')
                            else:
                                logger.error('profile | 详情种子获取失败')
                                # 队列一条任务
                                self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                continue
                        else:
                            logger.error('catalog | 论文{}年{}期列表页获取失败'.format(qikan_year[0], qikan_year[1]))
                            # 队列一条任务
                            self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                            continue
                    else:
                        logger.info('catalog | 年、期列表获取完毕')

            else:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return

    def queue_catalog(self):
        while True:
            # 查询redis队列中任务数量
            url_number = self.dao.select_task_number(key=config.REDIS_QIKAN_CATALOG)
            if url_number <= config.MAX_QUEUE_REDIS/10:
                logger.info('queue | redis中任务已少于 {}, 开始新增队列任务'.format(int(config.MAX_QUEUE_REDIS / 10)))
                # 获取任务
                new_task_list = self.dao.get_task_list_from_mysql(table=config.MYSQL_MAGAZINE, ws='中国知网', es='期刊', count=15000)
                # print(new_task_list)
                # 队列任务
                self.dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_QIKAN_CATALOG, data=new_task_list)
            else:
                logger.info('queue | redis剩余{}个任务'.format(url_number))

            time.sleep(1)


def queue_task():
    main = SpiderMain()
    try:
        main.queue_catalog()
    except:
        logger.exception(str(traceback.format_exc()))


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
    tpool = ThreadPoolExecutor(max_workers=1)
    for i in range(1):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    # process_start()
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=1)
    # ppool.submit(queue_task)
    for i in range(1):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
