# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import mysqlpool_utils


class Dao_58TongCheng(object):
    def __init__(self):
        # mysql存储公司名的表名
        self.company_name_table = 'ss_company'

    # 存储公司名称
    def saveCompanyName(self, logging, mysql_client, data):
        for name in data:
            sha = hashlib.sha1(name.encode('utf-8')).hexdigest()
            # 查询当前数据是否已存在
            sql = "select * from ss_company where sha = '{}'".format(sha)
            data_status = mysqlpool_utils.execute(connection=mysql_client, sql=sql)
            if data_status:
                logging.info('《{}》已存在'.format(name))
                continue
            save_data = {
                "sha": sha,
                "title": name
            }
            mysqlpool_utils.insert_one(connection=mysql_client, table=self.company_name_table, data=save_data)
            logging.info('《{}》保存成功'.format(name))

