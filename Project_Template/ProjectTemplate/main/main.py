# -*-coding:utf-8-*-

'''

'''
import sys
import os
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project_Template.ProjectTemplate.middleware import download_middleware
from Project_Template.ProjectTemplate.service import service
from Project_Template.ProjectTemplate.dao import dao
from Project_Template.ProjectTemplate import config

log_file_dir = ''  # LOG日志存放路径
LOGNAME = ''  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()


    def start(self):
        pass



def process_start():
    main = SpiderMain()
    main.start()

if __name__ == '__main__':
    po = Pool(config.PROCESS_NUMBER)
    for i in range(config.PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
