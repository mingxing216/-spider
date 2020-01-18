# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage


class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    # 保存任务url到mysql数据库
    def saveUrlToMysql(self, table, url):
        data = {
            'url': url
        }
        try:
            self.mysql_client.insert_one(table=table, data=data)
        except:
            pass
