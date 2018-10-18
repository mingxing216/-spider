# -*-coding:utf-8-*-
import os
import sys
import re
import requests
import hashlib
import pprint
import redis
import threading
import random
import time
import gc
import psutil
import threadpool
from redis import StrictRedis
from urllib.parse import urlparse
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Queue

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings

from utils import redis_dbutils
from utils import mysql_dbutils

def saddredis():
    redis_client = StrictRedis(host='60.195.249.105', port=6379, password='spider')

    with open('../config/redis_qikan_queue_2.txt', 'r') as f:
        datas = f.readlines()

    for i in datas:
        data = re.sub(r'\n', '', i)
        redis_client.sadd('qikan_queue_2', data)
        print(data)

saddredis()


# sql = 'select memo from ss_paper where sha = "1eaec2b85b9b61cd5117c8514d1164b284d15fd6"'
#
# mysql_server = mysql_dbutils.DBUtils_PyMysql()
# datas = mysql_server.get_results(sql)
# for data in datas:
#     print(data['memo'])



