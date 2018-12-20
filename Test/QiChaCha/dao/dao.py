# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import mysqlpool_utils
from Utils import redispool_utils


# 数据操作_基于登录
class Dao(object):
    def __init__(self):
        self.cookies_key = 'qiChaChaCookiePool' # 保存cookie的redis列表名
        self.company_qicha = 'ss_company_qicha' # 保存企查查任务的mysql表名
        self.objectKey = 'company_url_qicha'  # redis任务队列key

    # 获取cookie列表
    def getCookieList(self, logging, redis_client):
        cookie_list = redispool_utils.lrange(redis_client=redis_client, key=self.cookies_key, start=0, end=-1)

        return cookie_list

    # 保存企业url
    def saveCompanyUrl(self, logging, mysql_client, data):
        for company_url in data:
            # 生成sha1
            sha = hashlib.sha1(company_url.encode('utf-8')).hexdigest()

            # 查询当前数据是否已存在
            sql = "select * from {} where sha = '{}'".format(self.company_qicha, sha)
            data_status = mysqlpool_utils.execute(connection=mysql_client, sql=sql)
            if data_status:
                logging.info('企业种子已存在')
                continue
            save_data = {
                'sha': sha,
                'url': company_url
            }
            mysqlpool_utils.insert_one(connection=mysql_client, table=self.company_qicha, data=save_data)
            logging.info('企业种子保存成功')

    # 从redis获取任务
    def getObjectForRedis(self, logging, redis_client, count):
        obj_list = redispool_utils.queue_spops(redis_client=redis_client, key=self.objectKey,
                                               lockname='get_qicha_company_url_lock', count=count)

        logging.info('已获取企业任务: {}个'.format(len(obj_list)))
        return obj_list



