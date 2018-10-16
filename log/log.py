#-*-coding:utf-8-*-

'''
本文件提供log功能服务
'''

import logging
import time
import os
from logging import FileHandler
import traceback
import sys

sys.path.append(os.path.dirname(__file__) + os.sep + "../")

from utils import timeutils


class ILog(object):

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)

        # 获取当前日期
        now_date = timeutils.get_yyyy_mm_dd()
        # 添加handler
        # if not self.logger.handlers:
        #     filename = os.path.dirname(__file__) + os.sep + "../{}_{}.log".format(self.name, now_date)
        #     log_formatter = logging.Formatter('%(asctime)s {} %(levelname)s %(message)s'.format(self.name))
        #     log_handler = FileHandler(filename)
        #     log_handler.setFormatter(log_formatter)
        #     log_handler.suffix = '%Y%m%d'
        #     self.logger.addHandler(log_handler)
        #     self.logger.setLevel(logging.DEBUG)

    def info(self, msg):
        self.logger.info(str(msg))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " INFO " + str(msg))

    def error(self, msg):
        self.logger.info(str(msg))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " ERROR " + str(msg))

    def exception(self, e):
        self.logger.exception(e)

        msg = traceback.format_exc()
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " ERROR " + str(msg))
