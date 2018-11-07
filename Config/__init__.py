# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log

logname = ''
logging = log.ILog(logname)


class SpiderMain(object):
    def __init__(self):
        pass

    def run(self):
        pass


if __name__ == '__main__':
    main = SpiderMain()
    main.run()