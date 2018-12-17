# -*-coding:utf-8-*-
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import redispool_utils
from Utils import mysqlpool_utils


class SpiderMain(object):
    def __init__(self):
        pass

    def run(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()



if __name__ == '__main__':
    spider_main = SpiderMain()
    spider_main.run()