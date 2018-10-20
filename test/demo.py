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
import pymysql
from redis import StrictRedis
from urllib.parse import urlparse
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Queue

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings

from utils import redis_dbutils
from utils import mysql_dbutils

# def saddredis():
#     redis_client = StrictRedis(host='60.195.249.105', port=6379, password='spider')
#
#     with open('../config/redis_qikan_queue_2.txt', 'r') as f:
#         datas = f.readlines()
#
#     for i in datas:
#         data = re.sub(r'\n', '', i)
#         redis_client.sadd('qikan_queue_2', data)
#         print(data)
#
# saddredis()


# def get_connection():
#     conn = pymysql.connect(host='60.195.249.104',
#                            user='spider',
#                            password='spider',
#                            database=settings.DB_NAME,
#                            port=3306,
#                            charset="utf8mb4",
#                            cursorclass=pymysql.cursors.DictCursor)
#     return conn
#
# conn = get_connection()
# cur = conn.cursor()
# sql = 'select memo from ss_paper where sha = "01492e80fe369fae5d22c9b9bd1d6822db3faa26"'
# cur.execute(sql)
# ret = cur.fetchall()
# cur.close()
# conn.close()
#
# for data in ret:
#     print(data['memo'])


i = 1
for i in range(12):
    if (i + 1) % 3 == 0:
        print('yes: {}'.format(i))

    else:
        print('no: {}'.format(i))



