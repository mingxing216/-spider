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

    # 种子字典存入数据库
    def saveProjectUrlToMysql(self, table, memo):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        ctx = str(memo).replace('\'', '"')
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'ctx': ctx,
                'url': url,
                'es': 'qikan',
                'ws': 'jstor',
                'date_created': timeutils.getNowDatetime()
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info('已存储种子: {}'.format(url))
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('种子已存在: {}'.format(sha))
