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
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<期刊论文_期刊_queue>'  # LOG名
NAME = '期刊论文_期刊_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False # 爬虫名入库
INSERT_DATA_NUMBER = False # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_QiKan(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.select_task_number(key=config.REDIS_QIKAN_MAGAZINE)
            if url_number == 0:
                LOGGING.info('redis已无任务，准备开始队列任务。')
                # 获取任务
                new_task_list = self.dao.get_task_list_from_mysql(table=config.MYSQL_MAGAZINE, ws='中国知网', es='期刊论文', count=10000)
                # print(new_task_list)
                # 队列任务
                self.dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_QIKAN_MAGAZINE, data=new_task_list)
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
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
