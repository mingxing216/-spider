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

redis_host = '60.195.249.104'
redis_port = 6379
redis_pass = 'spider'

sr = StrictRedis(host=redis_host, port=redis_port, password=redis_pass)

data = sr.smembers('proxy')

with open('../config/redis_article_qikan_queue_2.txt', 'r') as f:
    datas = f.readlines()

for i in datas:
    i = re.sub(r'\n', '', i)
    sr.sadd('article_qikan_queue_2', i)
    print(i)
