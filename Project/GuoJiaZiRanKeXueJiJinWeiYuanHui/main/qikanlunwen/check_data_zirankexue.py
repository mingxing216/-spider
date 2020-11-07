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

from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import user_pool, hbase_pool, timeutils

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"

# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/ZiRanKeXue/全文_check_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")


class BastSpiderMain(object):
    def __init__(self):
        # 下载中间件
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=logger)
        # 存储
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)
        # hbase存储对象
        self.hbase_obj = hbase_pool.HBasePool(logging=logger)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.num = 0

    def __get_resp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        """

        :type referer: basestring
        """
        # 发现验证码，请求页面3次
        for _i in range(3):
            resp = self.download_middleware.getResp(url, method, s=s, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges)
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
        pdf_url = task_data.get('pdfUrl')
        if pdf_url:
            pdf_sha = hashlib.sha1(pdf_url.encode('utf-8')).hexdigest()
            _id = task_data.get('fulltext')
            paper_url = task_data.get('url')
            paper_sha = task_data.get('sha')

            # 获取hbase中全文数据
            info_dict = self.hbase_obj.get_one_data_from_hbase(pdf_sha)

            if info_dict is not None:
                if b'm:content' not in info_dict.keys():
                    # 更新全文种子错误信息及状态
                    msg = '全文content字段缺失, url: {}'.format(pdf_url)
                    logger.warning(msg)
                    data = {
                        'del': '0',
                        'msg': msg,
                        'date_created': timeutils.getNowDatetime()
                    }
                    self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)

                elif not info_dict.get(b'm:content'):
                    # 更新全文种子错误信息及状态
                    msg = '全文content字段无值, url: {}'.format(pdf_url)
                    logger.warning(msg)
                    data = {
                        'del': '0',
                        'msg': msg,
                        'date_created': timeutils.getNowDatetime()
                    }
                    self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)

                else:
                    begin_time = time.time()
                    info_bs64 = info_dict.get(b'm:content').decode('utf-8')
                    # print(info_bs64)
                    info = base64.b64decode(info_bs64)
                    # print(info)
                    logger.info('handle | 全文base64转二进制 | use time: {}'.format('%.3f' % (time.time() - begin_time)))

                    # 检测PDF文件
                    is_value = self.is_valid_pdf_bytes_io(info)
                    if not is_value:
                        # 更新全文种子错误信息及状态
                        msg = 'not PDF, url: {}'.format(pdf_url)
                        logger.warning(msg)
                        data = {
                            'del': '0',
                            'msg': msg,
                            'date_created': timeutils.getNowDatetime()
                        }
                        self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)
                    else:
                        # 记录全文正确信息
                        msg = 'is PDF, url: {}'.format(pdf_url)
                        logger.info(msg)
                        data = {
                            'del': '3',
                            'msg': msg,
                            'date_created': timeutils.getNowDatetime()
                        }
                        self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)

            else:
                msg = '全文数据获取失败, url: {}'.format(pdf_url)
                logger.warning(msg)
                data = {
                    'del': '0',
                    'msg': msg,
                    'date_created': timeutils.getNowDatetime()
                }
                self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=paper_sha)

        else:
            msg = '无全文PDF, url: {}'.format(task_data.get('url'))
            logger.warning(msg)
            data = {
                'del': '1',
                'msg': msg,
                'date_created': timeutils.getNowDatetime()
            }
            self.dao.update_task_to_mysql(table=config.MYSQL_PAPER, data=data, sha=task_data.get('sha'))

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
            task = self.dao.get_one_task_from_redis(key=config.REDIS_ZIRANKEXUE_PAPER)
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
