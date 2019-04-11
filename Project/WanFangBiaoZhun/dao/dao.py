# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage


class Task_Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Task_Dao, self).__init__(logging=logging,
                                       mysqlpool_number=mysqlpool_number,
                                       redispool_number=redispool_number)


class Data_Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Data_Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

