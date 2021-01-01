# -*- coding:utf-8 -*-
import base64
import os
import sys
import hashlib
import json
import random
import re
import time
import traceback

# import gevent
# from gevent import monkey
# monkey.patch_all()
# from contextlib import closing
from io import BytesIO
from multiprocessing.pool import Pool, ThreadPool
from PyPDF2 import PdfFileReader
from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import user_pool, hbase_pool, timeutils

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"

# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/SheHuiKeXue/全文_check_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")


class BastSpiderMain(object):
    def __init__(self):
        # cookie池
        self.cookie_obj = user_pool.CookieUtils(logging=logger)
        # 下载中间件
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY,
                                                                  cookie_obj=self.cookie_obj)
        # self.server = service.Server(logging=LOGGING)
        # 存储
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.num = 0
        self.f = open('nssd_test_data.txt', 'a+')
        self.f_fulltext = open('nssd_fulltext_data.txt', 'a+')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()

    def __get_resp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None, user=None):
        """

        :type referer: basestring
        """
        # 发现验证码，请求页面3次
        for _i in range(3):
            resp = self.download_middleware.getResp(url, method, s=s, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges, user=user)
            # if resp and resp.headers['Content-Type'].startswith('text'):
            #     if '请输入验证码' in resp.text:
            #         print('请重新登录')
            #         LOGGING.error('出现验证码: {}'.format(url))
            #         continue
            return resp
        else:
            return

    # 检测PDF文件正确性
    @staticmethod
    def is_valid_pdf_bytes_io(content):
        b_valid = True
        try:
            reader = PdfFileReader(BytesIO(content), strict=False)
            if reader.getNumPages() < 1:  # 进一步通过页数判断。
                b_valid = False
        except:
            logger.error(str(traceback.format_exc()))
            b_valid = False

        return b_valid

    def handle(self, task_data):
        # 判断是否有全文url
        self.num += 1
        paper_url = task_data.get('url')
        if paper_url:
            _id = re.findall(r"id=(.*)?&?", paper_url)[0]
            key = 'nssd.org|' + _id
            paper_entity_sha = hashlib.sha1(key.encode('utf-8')).hexdigest()
            paper_sha = task_data.get('sha')

            # 获取hbase中全文数据
            info_dict = self.dao.get_data_from_hbase(paper_entity_sha, '论文')
            if info_dict:
                # # 更新全文种子错误信息及状态
                # msg = 'hbase有该实体数据, sha: {}'.format(paper_sha)
                # logger.info(msg)
                # data = {
                #     'del': '5',
                #     'date_created': timeutils.getNowDatetime()
                # }
                # self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)

                info_str = json.dumps(info_dict, ensure_ascii=False)

                self.f.write(paper_entity_sha + '\t' + info_str + '\n')

                logger.info('{} 论文实体数据写入文本成功, url: {}'.format(self.num, paper_url))

            else:
                logger.warning('{} 无论文实体数据, url: {}'.format(self.num, paper_url))

        fulltext_url = task_data.get('pdfUrl')
        if fulltext_url:
            sha = hashlib.sha1(fulltext_url.encode('utf-8')).hexdigest()
            dict = self.dao.get_media_from_hbase(sha, 'document')
            if dict:
                # # 更新全文种子错误信息及状态
                # msg = 'hbase有该实体数据, sha: {}'.format(paper_sha)
                # logger.info(msg)
                # data = {
                #     'del': '5',
                #     'date_created': timeutils.getNowDatetime()
                # }
                # self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)


                self.f_fulltext.write(sha + '\t' + json.dumps(dict, ensure_ascii=False) + '\n')

                logger.info('{} 论文全文数据写入文本成功, url: {}'.format(self.num, fulltext_url))

            else:
                logger.warning('{} 无论文全文数据, url: {}'.format(self.num, fulltext_url))

    def run(self):
        logger.info('线程启动')
        # 第一次请求的等待时间
        delay_time = time.time()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.info('handle | download delay | use time: {}'.format('%.3f' % (time.time() - delay_time)))
        # 单线程无限循环
        while True:
            # 获取任务
            start_time = time.time()
            task = self.dao.get_one_task_from_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER)
            if task:
                try:
                    # json数据类型转换
                    task_data = json.loads(task)
                    # 获取全文数据并判断是否正确
                    self.handle(task_data=task_data)

                    logger.info('handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))

                except:
                    logger.error(str(traceback.format_exc()))
                    logger.info('handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))
            else:
                logger.info('队列中已无任务')

    def start(self):
        # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

        # # 创建gevent协程
        # g_list = []
        # for i in range(8):
        #     s = gevent.spawn(self.run)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        thread_pool = ThreadPool(processes=config.THREAD_NUM)
        for thread_index in range(config.THREAD_NUM):
            thread_pool.apply_async(func=self.run)

        thread_pool.close()
        thread_pool.join()

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task="{'id': '207d122a-3a68-41b1-8d8a-f20552f22054', 'xueKeLeiBie': '信息科学部', 'url': 'http://ir.nsfc.gov.cn/paperDetail/207d122a-3a68-41b1-8d8a-f20552f22054'}")
    except:
        logger.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    # process_start()
    # 创建多进程
    po = Pool(processes=config.PROCESS_NUM)
    for _count in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
