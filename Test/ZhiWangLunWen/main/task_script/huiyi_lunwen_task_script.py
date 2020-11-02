# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
from multiprocessing import Process

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import mysql_pool
from Utils import redis_pool
from Test.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_会议论文_queue>'  # LOG名
NAME = '知网_会议论文_queue'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

# 生成任务队列
def createTask(redis_table, redis_max, redis_min, mysql_table, data_type, script_name):
    mysql_client = mysql_pool.MysqlPool(number=1)
    redis_client = redis_pool.RedisPoolUtils(number=1)

    while 1:
        set_number_now = redis_client.scard(key=redis_table)
        if set_number_now <= redis_min:
            count = redis_max - set_number_now

            select_sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(mysql_table, data_type, count)
            data_list = mysql_client.get_results(sql=select_sql)
            if data_list:
                LOGGING.info('已从mysql获取{}个{}任务。'.format(len(data_list), script_name))
                for data in data_list:
                    data['create_at'] = str(data['create_at'])
                    redis_client.sadd(key=redis_table, value=str(data))

                time.sleep(1)

            else:
                LOGGING.warning('mysql无{}数据'.format(script_name))
                time.sleep(10)
                continue
        else:
            time.sleep(1)


if __name__ == '__main__':
    p1 = Process(target=createTask,
                 kwargs={"redis_table": config.REDIS_HUIYILUNWEN_LUNWEN,
                         "redis_max": 2000,
                         "redis_min": 0,
                         "mysql_table": config.LUNWEN_URL_TABLE,
                         "data_type": 'huiyi',
                         "script_name": '会议论文种子'})
    p2 = Process(target=createTask,
                 kwargs={"redis_table": config.REDIS_QIKANLUNWEN_LUNWEN,
                         "redis_max": 2000,
                         "redis_min": 0,
                         "mysql_table": config.LUNWEN_URL_TABLE,
                         "data_type": 'qikan',
                         "script_name": '期刊论文种子'})

    p1.start()
    p2.start()
    p1.join()
    p2.join()

