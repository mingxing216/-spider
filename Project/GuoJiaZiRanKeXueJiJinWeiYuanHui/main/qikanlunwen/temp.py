# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
from io import BytesIO
import traceback
import hashlib
import random
import requests
from datetime import datetime
import json
import threading
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


log_file_dir = 'ZiRanKeXue'  # LOG日志存放路径
LOGNAME = '<国家自然科学_论文_data>'  # LOG名
NAME = '国家自然科学_论文_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

        self.profile_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperInfo'

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp and resp.headers['Content-Type'].startswith('text'):
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码: {}'.format(url))
                    continue

            return resp

        else:
            return

    # 获取文档实体字段
    def document(self):
        # 设置请求头
        headers = {
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'Accept-Encoding': 'gzip, deflate, br',
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            # 'Content-Type': 'application/json',
            'Connection': 'close',
            # 'Host': 'http://www.chinabgao.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
        }

        for i in range(3):
            start_time = time.time()
            try:
                resp = requests.get(url='http://ir.nsfc.gov.cn/paperDownload/1000014389375.pdf', headers=headers, stream=True, timeout=(3, 5))
                print(resp)
                print(resp.status_code)

                bytes_container = BytesIO()
                time_begin = time.time()

                for chunk in resp.iter_content(chunk_size=1024):
                    time_end = time.time()
                    if time_end - time_begin >= 2:
                        LOGGING.info("RequestTooLong Timeout")
                        return

                    time_begin = time_end
                    bytes_container.write(chunk)

                resp_content = bytes_container.getvalue()
                print(resp_content)
                LOGGING.info("handle | use time: {} | length: {} | code: 0 | status: {} | message: OK".format('%.3fs' % (time.time() - start_time), resp.headers['Content-Length'], resp.status_code))

            except requests.exceptions.RequestException as e:
                LOGGING.info("handle | use time: {} | code: 2 | status: NO | message: {}".format('%.3fs' % (time.time() - start_time), e))

            except Exception as e:
                LOGGING.info("handle | use time: {} | code: 2 | status: NO | message: {}".format('%.3fs' % (time.time() - start_time), e))

        # # 获取页面响应
        # pdf_resp = self.__getResp(url='http://ir.nsfc.gov.cn/paperDownload/1000014389375.pdf', method='GET')

    def start(self):
        # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

        # # 创建gevent协程
        # g_list = []
        # for i in range(8):
        #     s = gevent.spawn(self.run)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        self.document()

        # # 创建线程池
        # threadpool = ThreadPool(processes=config.THREAD_NUM)
        # for i in range(config.THREAD_NUM):
        #     threadpool.apply_async(func=self.run)
        #
        # threadpool.close()
        # threadpool.join()

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task="{'id': '207d122a-3a68-41b1-8d8a-f20552f22054', 'xueKeLeiBie': '信息科学部', 'url': 'http://ir.nsfc.gov.cn/paperDetail/207d122a-3a68-41b1-8d8a-f20552f22054'}")
    except:
        LOGGING.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()

    # po = Pool(processes=config.PROCESS_NUM)
    # for i in range(config.PROCESS_NUM):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('====== Time consuming is %.2fs ======' %(end_time - begin_time))
