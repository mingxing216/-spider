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
from utils import redispool_utils

redis_client = redispool_utils.createRedisPool()



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
#     conn = pymysql.connect(host='127.0.0.1',
#                            user='root',
#                            password='rockerfm520',
#                            database=settings.DB_NAME,
#                            port=3306,
#                            charset="utf8mb4",
#                            cursorclass=pymysql.cursors.DictCursor)
#     return conn
#
# conn = get_connection()
# cur = conn.cursor()
# sql = 'select * from ss_magazine where sha = "0001e4dba766bfacff637ad2ca71192fa6557544"'
# cur.execute(sql)
# ret = cur.fetchall()
# cur.close()
# conn.close()
#
# for data in ret:
#     print(data['memo'])



# from multiprocessing import Pool, Manager, Queue
#
# q = Manager().Queue()
# for i in range(10000):
#     q.put(i)
#
# def A(ii):
#     while True:
#         data = []
#         for i in range(100):
#             if q.qsize() != 0:
#                 try:
#                     a = q.get_nowait()
#                 except:
#                     break
#                 else:
#                     data.append(a)
#         if not data:
#             break
#         else:
#             print('进程{}，　{}'.format(ii, len(data)))
#
#
# pool = Pool(4)
# for ii in range(4):
#     pool.apply_async(func=A, args=(ii,))
#
# pool.close()
# pool.join()



