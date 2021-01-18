# -*- coding:utf-8 -*-
import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import requests

from Log import logging
from Utils import user_agent_u
from Utils.captcha import RecognizeCode

LOG_FILE_DIR = 'Test'  # LOG日志存放路径
LOG_NAME = 'test_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class CaptchaTest(object):
    def  __init__(self):
        self.captcha = RecognizeCode(logger)

    def get_img_content(self):
        headers = {'User-Agent': user_agent_u.get_ua()}
        content = requests.get('http://103.247.176.188/ImgCode.aspx', headers=headers, timeout=30).content
        return content

    def run(self, content):
        while True:
            code = self.captcha.image_data(image_data=content, show=False, length=4,
                                           invalid_charset="^0-9^A-Z^a-z")
            logger.info('code: {}'.format(code))


def start():
    test = CaptchaTest()
    content = test.get_img_content()
    test.run(content)


def process_start():
    # 创建线程池
    tpool = ThreadPoolExecutor(max_workers=32)
    for i in range(32):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=8)
    for i in range(8):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
