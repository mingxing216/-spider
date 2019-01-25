# -*-coding:utf-8-*-
'''
redis多账号池生成脚本
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
        # 查询mysql账号数量
        mobile_number = len(mobile_list)
        if mobile_number == 0:
            print('mysql无大为账号')
            return
        # 判断当前账号数量能否平均分为5份
        number = mobile_number % self.redis_mobilepool_sum
        if number == 0:
            data_number = mobile_number / self.redis_mobilepool_sum # 每个redis账号池内的账号数量
        else:
            data_number = int(mobile_number / self.redis_mobilepool_sum) + 1 # 每个redis账号池内的账号数量
        first_data_number = 0
        for redis_pool_number in range(self.redis_mobilepool_sum):
            redis_pool_number += 1 # 规避账号池编号为0
            if redis_pool_number == 1:
                redis_key = 'innojoy_mobilepool_url_spider' # 抓取专利种子专用账号池
            else:
                redis_key = 'innojoy_mobilepool_data_spider{}'.format(redis_pool_number - 1) # 抓取专利详情专用账号池
            # 存储账号到redis账号池
            mobile_data = mobile_list[first_data_number:redis_pool_number * data_number]
            self.createMobileQueue(redis_client=redis_client, key=redis_key, data=mobile_data)
            first_data_number += len(mobile_data)


if __name__ == '__main__':
    scrapt = ScraptMain()
    scrapt.run()