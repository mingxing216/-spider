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
from redis import StrictRedis
from urllib.parse import urlparse
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings

from utils import redis_dbutils

# def inputdata():
#     for i in range(1000):
#         redis_dbutils.saveSet('comlieted', i)
#
# inputdata()

def demo():
    while True:
        a = redis_dbutils.spop(key='comlieted', lockname='spop_demo')
        if a:
            print(a)
        else:
            break

po = Pool(4)
for i in range(4):
    po.apply_async(func=demo)

po.close()
po.join()

