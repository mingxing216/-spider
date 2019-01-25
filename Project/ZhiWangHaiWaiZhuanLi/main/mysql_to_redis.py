# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Project.ZhiWangHaiWaiZhuanLi import config
from Utils import mysqlpool_utils
from Utils import redis_pool

mysql_client = mysqlpool_utils.MysqlPool()
redis_client = redis_pool.RedisPoolUtils()

while 1:
    # 查询redis队列中任务数量
    url_number = redis_client.scard(key=config.REDIS_URL_TABLE)
    if url_number <= 800:
        print('任务数少于100, 开始队列任务')
        # 获取1000个任务
        select_sql = "select * from {} limit 1000".format(config.MYSQL_URL_TABLE)
        datalist = mysql_client.get_results(sql=select_sql)
        if datalist:
            for url_data in datalist:
                url = url_data['url']
                # 队列至任务至redis数据库
                redis_client.sadd(key=config.REDIS_URL_TABLE, value=url)

        else:
            print('mysql无任务, 10秒后重试')
            time.sleep(10)

    else:
        print('任务数大于100, 等待重新查询')
        time.sleep(10)


