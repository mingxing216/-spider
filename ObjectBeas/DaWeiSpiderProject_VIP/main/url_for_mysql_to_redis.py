# -*-coding:utf-8-*-
'''
从mysql获取1000个url任务队列至redis数据库
'''
import os
import sys
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Utils import redispool_utils
from Utils import mysql_dbutils


class StartMain(object):
    def __init__(self):
        self.redis_key = 'innojoy_patent_url'
        self.mysql_table = 'ss_innojoy_patent_url'

    def run(self):
        while 1:
            redis_client = redispool_utils.createRedisPool()
            mysql_client = mysql_dbutils.DBUtils_PyMysql()
            # 查询redis队列中任务数量
            url_num = redispool_utils.scard(redis_client=redis_client, key=self.redis_key)
            if url_num < 100:
                # 从mysql获取1000条任务
                sql = 'select url from {} where del = "0" limit 1000'.format(self.mysql_table)
                url_list = mysql_client.get_results(sql=sql)
                for url in url_list:
                    url = url['url']
                    redispool_utils.sadd(redis_client=redis_client, key=self.redis_key, value=url)
                    # mysql逻辑删除任务
                    mysql_client.update(table=self.mysql_table, data={'del': 1}, where='url = "{}"'.format(url))

            time.sleep(10)


if __name__ == '__main__':
    start_main = StartMain()
    start_main.run()