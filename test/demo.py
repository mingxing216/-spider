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

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings

from utils import redis_dbutils

def func(url, ga):
    print(url)
    print(ga)

po = ThreadPool(2)
for i in range(2):
    po.apply_async(func=func, args=(1, 2))
po.close()
po.join()

