# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.IHSmarkit.middleware import download_middleware
from Project.IHSmarkit.service import service
from Project.IHSmarkit.dao import dao
from Project.IHSmarkit import config

log_file_dir = 'IHSmarkit'  # LOG日志存放路径
LOGNAME = 'IHSmarkit_机构_queue'  # LOG名
NAME = 'IHSmarkit_机构_queue'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False # 爬虫名入库
INSERT_DATA_NUMBER = False # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.JiGouServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.selectTaskNumber(key=config.REDIS_INSTITUTE)
            if url_number == 0:
                LOGGING.info('redis已无任务，准备开始队列任务。')

                # 获取任务
                new_task_list = self.dao.getNewTaskList(table=config.MYSQL_INSTITUTE, count=2000)
                # print(new_task_list)
                LOGGING.info('已从Mysql获取到{}个任务'.format(len(new_task_list)))

                # 队列任务
                self.dao.QueueTask(key=config.REDIS_INSTITUTE, data=new_task_list)
                LOGGING.info('已成功向redis队列{}个任务'.format(len(new_task_list)))
            else:
                LOGGING.info('redis剩余{}个任务'.format(url_number))

            time.sleep(1)


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()

    process_start()

    # po = Pool(1)
    # for i in range(1):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
