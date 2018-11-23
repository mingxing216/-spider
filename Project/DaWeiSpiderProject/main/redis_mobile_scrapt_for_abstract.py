# -*-coding:utf-8-*-
'''
单账号池生成脚本——主要针对摘要抓取爬虫
'''
import os
import sys

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import mysqlpool_utils
from Utils import redispool_utils


class ScraptMain(object):
    def __init__(self):
        self.innojoy_mobile_table = 'ss_innojoy_mobile' # mysql中存储innojoy账号的表名
        self.redis_mobilepool_sum = 5 # redis中账号池数量

    # 从mysql获取innojoy账号
    def getInnojoyMobile(self, connection):
        sql = 'select mobile from ss_innojoy_mobile'
        mobiles_list = mysqlpool_utils.get_results(connection=connection, sql=sql)

        return mobiles_list

    # 将innojoy账号队列至redis数据库
    def createMobileQueue(self, redis_client, key, data):
        for mobiles in data:
            mobile = mobiles['mobile']
            redispool_utils.sadd(redis_client=redis_client, key=key, value=mobile)

    def run(self):
        redis_client = redispool_utils.createRedisPool() # redis对象
        mysql_client = mysqlpool_utils.createMysqlPool() # mysql对象
        # 获取mysql中全部账号
        mobile_list = self.getInnojoyMobile(connection=mysql_client)
        # 将innojoy账号队列至redis数据库
        self.createMobileQueue(redis_client=redis_client, key='innojoy_mobilepool_url_spider', data=mobile_list)


if __name__ == '__main__':
    scrapt = ScraptMain()
    scrapt.run()