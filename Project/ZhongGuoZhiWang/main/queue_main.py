# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangHaiWaiZhuanLi.middleware import download_middleware
from Project.ZhiWangHaiWaiZhuanLi.service import service
from Project.ZhiWangHaiWaiZhuanLi.dao import dao
from Project.ZhiWangHaiWaiZhuanLi import config

log_file_dir = 'ZhiWangHaiWaiZhuanLi'  # LOG日志存放路径
LOGNAME = '<知网_海外专利_queue>'  # LOG名
NAME = '知网_海外专利_queue'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False # 爬虫名入库
INSERT_DATA_NUMBER = False # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.Server(logging=LOGGING)
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
            url_number = self.dao.selectTaskNumber(key=config.REDIS_TASK)
            if url_number == 0:
                LOGGING.info('redis已无任务，准备开始队列任务。')

                # 获取任务
                new_task_list = self.dao.getNewTaskList(table=config.MYSQL_TASK, count=2000)
                LOGGING.info('已从Mysql获取到{}个任务'.format(len(new_task_list)))

                # 队列任务
                self.dao.QueueTask(key=config.REDIS_TASK, data=new_task_list)
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
    po = Pool(1)
    for i in range(1):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
