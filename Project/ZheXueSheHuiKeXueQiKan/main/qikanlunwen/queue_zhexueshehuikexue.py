# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing.pool import Pool, ThreadPool
from loguru import logger

# sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"
# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/SheHuiKeXue/期刊论文_queue_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.select_task_number(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER)
            if url_number <= config.MAX_QUEUE_REDIS/10:
                logger.info('redis中任务已少于 {}, 开始新增队列任务'.format(int(config.MAX_QUEUE_REDIS / 10)))
                # 获取任务
                new_task_list = self.dao.get_task_list_from_mysql(table=config.MYSQL_PAPER, ws='国家哲学社会科学', es='期刊论文', count=config.MAX_QUEUE_REDIS)
                # print(new_task_list)
                # 队列任务
                self.dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER, data=new_task_list)
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
    logger.info('======Time consuming is %.2fs======' % (end_time - begin_time))
