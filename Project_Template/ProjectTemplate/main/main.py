# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project_Template.ProjectTemplate.middleware import download_middleware
from Project_Template.ProjectTemplate.service import service
from Project_Template.ProjectTemplate.dao import dao
from Project_Template.ProjectTemplate import config

log_file_dir = ''  # LOG日志存放路径
LOGNAME = ''  # LOG名
NAME = '' # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)
        # 数据库录入爬虫名
        self.dao.saveSpiderName(name=NAME)

class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()


    def start(self):
        pass



def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.PROCESS_NUMBER)
    for i in range(config.PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
