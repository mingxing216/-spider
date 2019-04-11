# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Project.TaskScrapt.middleware import download_middleware
from Project.TaskScrapt.service import service
from Project.TaskScrapt.dao import dao
from Project.TaskScrapt import config

log_file_dir = 'TaskScript'  # LOG日志存放路径
LOGNAME = '<任务队列脚本>'  # LOG名
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
        while 1:
            # 获取cateid列表
            cateid_list = self.dao.getCateidList(table=settings.TASK_TABLE)

            for cateid_dict in cateid_list:

                # 将cateid转换成拼音
                cateid = cateid_dict['cateid']
                cateid_pinyin = self.server.getCateidPinyin(cateid)

                # 查询redis中任务数量
                task_number = self.dao.getTaskNumber_Redis(cateid_pinyin=cateid_pinyin)

                # 如果redis中任务数量为0，从Mysql拉取对应任务到redis
                if task_number == 0:
                    # 从Mysql获取任务
                    m_task = self.dao.getM_Task(table=settings.TASK_TABLE, cateid=cateid)
                    # 将Mysql任务缓存到redis
                    self.dao.insertTaskToRedis(key=cateid_pinyin, m_task=m_task)

                else:
                    continue

            time.sleep(1)
            continue


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
