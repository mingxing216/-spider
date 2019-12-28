# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
from multiprocessing import Process

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import mysqlpool_utils
from Utils import redis_pool
from Project.ZhiWangLunWen import config


log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<redis任务队列>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


# 生成任务队列
def createTask(redis_table, redis_max, redis_min, mysql_table, data_type):
    mysql_client = mysqlpool_utils.MysqlPool(number=1)
    redis_client = redis_pool.RedisPoolUtils(number=1)

    while 1:
        set_number_now = redis_client.scard(key=redis_table)
        if set_number_now <= redis_min:
            count = redis_max - set_number_now

            select_sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(mysql_table, data_type, count)
            data_list = mysql_client.get_results(sql=select_sql)
            if data_list:
                LOGGING.info('已从mysql获取{}个任务。'.format(len(data_list)))
                for data in data_list:
                    data['create_at'] = str(data['create_at'])
                    redis_client.sadd(key=redis_table, value=str(data))

                time.sleep(1)

            else:
                LOGGING.warning('mysql无数据')
                time.sleep(10)
        else:
            time.sleep(1)


if __name__ == '__main__':
    # 期刊论文_期刊队列
    P1 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_QIKANLUNWEN_QIKAN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_QIKAN,
        'data_type': config.QIKANLUNWEN_QIKAN_MAIN
    })
    # 会议论文_期刊任务
    P2 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_HUIYILUNWEN_QIKAN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_QIKAN,
        'data_type': config.HUIYILUNWEN_QIKAN_MAIN
    })
    # 学位论文_期刊任务
    P3 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_XUEWEILUNWEN_QIKAN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_QIKAN,
        'data_type': config.XUEWEILUNWEN_QIKAN_MAIN
    })
    # 期刊论文_论文队列
    P4 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_QIKANLUNWEN_LUNWEN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_LUNWEN,
        'data_type': config.QIKANLUNWEN_LUNWEN_MAIN
    })
    # 会议论文_论文队列
    P5 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_HUIYILUNWEN_LUNWEN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_LUNWEN,
        'data_type': config.HUIYILUNWEN_LUNWEN_MAIN
    })
    # 学位论文_论文队列
    P6 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_XUEWEILUNWEN_LUNWEN,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_LUNWEN,
        'data_type': config.XUEWEILUNWEN_LUNWEN_MAIN
    })
    # 机构队列
    P7 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_JIGOU,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_JIGOU,
        'data_type': '中国知网'
    })
    # 作者队列
    P8 = Process(target=createTask, kwargs={
        'redis_table': config.REDIS_ZUOZHE,
        'redis_max': config.REDIS_MAX,
        'redis_min': config.REDIS_MIN,
        'mysql_table': config.MYSQL_ZUOZHE,
        'data_type': '中国知网'
    })
    # P1.start()
    # P2.start()
    # P3.start()
    # P4.start()
    P5.start()
    # P6.start()
    # P7.start()
    P8.start()
    # P1.join()
    # P2.join()
    # P3.join()
    # P4.join()
    P5.join()
    # P6.join()
    # P7.join()
    P8.join()


