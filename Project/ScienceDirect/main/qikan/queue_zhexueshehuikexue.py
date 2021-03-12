# -*- coding:utf-8 -*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing.pool import Pool, ThreadPool

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Project.ScienceDirect.middleware import download_middleware
from Project.ScienceDirect.service import service
from Project.ScienceDirect.dao import dao
from Project.ScienceDirect import config

LOG_FILE_DIR = 'ScienceDirect'  # LOG日志存放路径
LOG_NAME = '英文期刊_queue'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.select_task_number(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE)
            if url_number <= config.MAX_QUEUE_REDIS/10:
                logger.info('redis中任务已少于 {}, 开始新增队列任务'.format(int(config.MAX_QUEUE_REDIS/10)))
                # 获取任务
                new_task_list = self.dao.get_task_list_from_mysql(table=config.MYSQL_MAGAZINE, ws='英文哲学社会科学', es='期刊', count=config.MAX_QUEUE_REDIS)
                # print(new_task_list)
                # 队列任务
                self.dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE, data=new_task_list)
            else:
                logger.info('redis剩余{}个任务'.format(url_number))

            time.sleep(1)


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        logger.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    process_start()
    # po = Pool(1)
    # for i in range(1):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('======Time consuming is %.3fs======' %(end_time - begin_time))
