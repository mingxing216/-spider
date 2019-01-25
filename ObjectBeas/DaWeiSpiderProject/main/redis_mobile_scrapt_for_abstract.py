# -*-coding:utf-8-*-
'''
单账号池生成脚本——主要针对摘要抓取爬虫
'''
import os
import sys

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import mysqlpool_utils
from Utils import redispool_utils
from Utils import timeutils


class ScraptMain(object):
    def __init__(self):
        self.innojoy_mobile_table = 'ss_innojoy_mobile' # mysql中存储innojoy账号的表名
        self.innojoy_mobilepool_url_spider = 'innojoy_mobilepool_url_spider' # Redis账号池
        self.redis_mobilepool_sum = 5 # redis中账号池数量

    # 从mysql获取innojoy账号
    def getInnojoyMobile(self, connection):
        # 获取今日日期
        start_date = timeutils.get_yyyy_mm_dd() + ' ' + '00:00:00'
        end_date = timeutils.get_yyyy_mm_dd() + ' ' + '23:00:00'
        sql = 'select * from ss_innojoy_mobile where update_created not BETWEEN "{}" and "{}" or update_created is NULL;'.format(start_date, end_date)
        mobiles_list = mysqlpool_utils.get_result(connection=connection, sql=sql)
        if mobiles_list:
            return mobiles_list
        else:
            return None

    # 将mysql中账号的update_created字段设置为明日日期
    def update_created(self, connection, mobile):
        # 获取明日日期
        tomorrow = timeutils.get_current_millis() + 86400
        tomorrow_date = timeutils.formatMillis(timestamp=tomorrow, format='%Y-%m-%d') + ' ' + '00:00:00'
        data = {'update_created': tomorrow_date}
        mysqlpool_utils.update(connection=connection, table=self.innojoy_mobile_table, data=data, where= "mobile = '{}'".format(mobile))

    # 将innojoy账号队列至redis数据库
    def createMobileQueue(self, redis_client, connection, key, data):
        # 清空redis账号池
        redispool_utils.delete(redis_client=redis_client, key=self.innojoy_mobilepool_url_spider)
        # 创建redis账号池
        for mobile_data in data:
            mobile = mobile_data['mobile']
            redispool_utils.sadd(redis_client=redis_client, key=key, value=mobile)
            # 将mysql中的账号update_created字段设置为明日日期
            self.update_created(connection=connection, mobile=mobile)



    def run(self):
        redis_client = redispool_utils.createRedisPool() # redis对象
        mysql_client = mysqlpool_utils.createMysqlPool() # mysql对象
        # 从mysql获取1000个账号
        mobile_list = self.getInnojoyMobile(connection=mysql_client)
        # 将innojoy账号队列至redis数据库
        self.createMobileQueue(redis_client=redis_client, connection=mysql_client, key=self.innojoy_mobilepool_url_spider, data=mobile_list)


if __name__ == '__main__':
    scrapt = ScraptMain()
    scrapt.run()
