# -*- coding:utf-8 -*-
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Utils.captcha import RecognizeCode

LOG_FILE_DIR = 'Test'  # LOG日志存放路径
LOG_NAME = 'test_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class CaptchaTest(object):
    def  __init__(self):
        self.captcha = RecognizeCode(logger)

    def run(self, file_name):
        while True:
            code = self.captcha.image_file(file_name=file_name, show=False, length=4,
                                           invalid_charset="^0-9^A-Z^a-z")
            logger.info('code: {}'.format(code))


def start():
    test = CaptchaTest()
    test.run('/Users/master/Desktop/aaa.png')


if __name__ == '__main__':
    # 创建线程池
    tpool = ThreadPoolExecutor(max_workers=8)
    for i in range(8):
        tpool.submit(start)
    tpool.shutdown(wait=True)