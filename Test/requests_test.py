# -*- coding:utf-8 -*-
import os
import random
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import requests

from Utils import user_agent_u
from Log import logging

LOG_FILE_DIR = 'Test'  # LOG日志存放路径
LOG_NAME = 'requests_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


def run():
    s = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
    while True:
        logger.info('开始请求')
        s.keep_alive = False  # 关闭多余连接
        try:
            res = s.get(url='https://www.baidu.com/', headers=headers, timeout=(5, 10))
            logger.info('response.status_code: {}'.format(res.status_code))

        except Exception as e:
            logger.error('requests error: {}'.format(e))

        time.sleep(1)


def process_start():
    # 创建线程池
    tpool = ThreadPoolExecutor(max_workers=128)
    for i in range(128):
        tpool.submit(run)
    tpool.shutdown()


if __name__ == '__main__':
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=1)
    for i in range(1):
        ppool.submit(process_start)
    ppool.shutdown()
