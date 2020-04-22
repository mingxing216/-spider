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
LOGNAME = '<知网_作者_queue>'  # LOG名
NAME = '知网_作者_queue'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False # 爬虫名入库
INSERT_DATA_NUMBER = False # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.ZhiWangLunWen_ZuoZhe(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.selectTaskNumber(key=config.REDIS_ZHIWANG_PEOPLE)
            if url_number == 0:
                LOGGING.info('redis已无任务，准备开始队列任务。')
                # 获取任务
                new_task_list = self.dao.getNewTaskList(table=config.MYSQL_PEOPLE, ws='中国知网', es='论文', count=1000)
                # print(new_task_list)
                # 队列任务
                self.dao.QueueTask(key=config.REDIS_ZHIWANG_PEOPLE, data=new_task_list)
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
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
