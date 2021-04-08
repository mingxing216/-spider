# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Storage import storage


class Dao(storage.Dao):
    def __init__(self, logging, host, port, user, pwd, db, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  host=host, port=port, user=user, pwd=pwd, db=db,
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
