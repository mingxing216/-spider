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

from Utils import timeutils
from Utils import dir_utils


class ILog(object):

    def haveLogDir(self, dirname):
        '''
        检查是否含有log文件夹
        :param dirname: 文件夹名字
        '''
        dir_path = str(os.path.dirname(__file__) + os.sep + "../../../../../opt/") + 'Log/' + dirname
        status = dir_utils.hasDir(dir_path)
        if status is False:
            dir_utils.createDir(dir_path)

    def __init__(self, file_dir, name):
        self.file_dir = file_dir
        self.name = name
        self.logger = logging.getLogger(name)

        self.haveLogDir(file_dir)
        # 获取当前日期
        now_date = timeutils.getNowDate()
        # 添加handler
        if not self.logger.handlers:
            filename = os.path.dirname(__file__) + os.sep + "../../../../../opt/Log/{}/{}_{}.log".format(self.file_dir, self.name, now_date)
            log_formatter = logging.Formatter('%(asctime)s {} %(levelname)s %(message)s'.format(self.name))
            log_handler = FileHandler(filename)
            log_handler.setFormatter(log_formatter)
            log_handler.suffix = '%Y%m%d'
            self.logger.addHandler(log_handler)
            self.logger.setLevel(logging.DEBUG)

    def info(self, msg):
        self.logger.info(str(msg))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " INFO " + str(msg))

    def error(self, msg):
        self.logger.error(str(msg))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " ERROR " + str(msg))

    def exception(self, e):
        self.logger.exception(e)

        msg = traceback.format_exc()
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " ERROR " + str(msg))

    def warning(self, msg):
        self.logger.warning(str(msg))

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.name + " " + now + " WARNING " + str(msg))


if __name__ == '__main__':
    demo = ILog('Template', 'spider_demo')


