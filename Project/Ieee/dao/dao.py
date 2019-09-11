# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import base64
from PIL import Image
from io import BytesIO
import hashlib
import requests
import re
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

import settings
from Utils import proxy
from Storage import storage
from Utils import timeutils

class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)
