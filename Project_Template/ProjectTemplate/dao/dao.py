# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage
from Utils import timeutils


class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

