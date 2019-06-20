# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import multiprocessing
import json
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import timeutils
from Test.ZhiWangLunWen.middleware import download_middleware
from Test.ZhiWangLunWen.service import service
from Test.ZhiWangLunWen.dao import dao
from Test.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_会议论文_task>'  # LOG名
NAME = '知网_会议论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False  # 爬虫名入库并记录抓取数据量

manage = multiprocessing.Manager()
TASK_Q = manage.Queue()


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_LunWenTaskServer(logging=LOGGING)
        self.dao = dao.HuiYiLunWen_LunWenTaskDao(logging=LOGGING,
                                                 mysqlpool_number=config.MYSQL_POOL_NUMBER,
                                                 redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class TaskMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        LOGGING.info('准备生成任务队列...')
        task_list = self.dao.getWenJiTask(table=config.QIKAN_URL_TABLE, data_type='huiyi')
        for task in task_list:
            TASK_Q.put(task)
        LOGGING.info('任务队列已生成，任务数: {}'.format(TASK_Q.qsize()))


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化会议列表页url
        self.huiyi_list_url = 'http://navi.cnki.net/knavi/DpaperDetail/GetDpaperListinPage'

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    # 开始程序
    def begin(self):
        while 1:
            # 从队列获取任务
            try:
                task = TASK_Q.get_nowait()
            except:
                task = None

            if not task:
                LOGGING.info('队列无任务')
                break

            self.start(task=task)

    def start(self, task):
        task_data = json.loads(task['memo'])
        task_url = task_data['url']
        task_jibie = task_data['jibie']

        # 获取pcode、lwjcode
        pcode, lwjcode = self.server.getPcodeAndLwjcode(data=task_url)
        if pcode is None or lwjcode is None:
            LOGGING.info('pcode、lwjcode参数获取失败')
            return

        # 生成会议数量页url
        huiyi_number_url = self.server.getHuiYiNumberUrl(pcode=pcode, lwjcode=lwjcode)
        # 获取会议数量页响应
        huiyi_number_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=huiyi_number_url,
                                           mode='GET')
        if not huiyi_number_resp:
            LOGGING.info('会议数量页响应获取失败')
            return

        huiyi_number_response = huiyi_number_resp.text
        # 获取会议数量
        huiyi_number = self.server.getHuiYiNumber(resp=huiyi_number_response)
        if huiyi_number <= 0:
            LOGGING.info('未获取到会议数量')
            return
        # 生成总页数
        page_number = self.server.getPageNumber(huiyi_number=huiyi_number)
        for page in range(page_number):
            # 生成会议列表页请求参数
            huiyi_list_url_data = self.server.getHuiYiListUrlData(pcode=pcode, lwjcode=lwjcode, page=page)
            # 获取会议列表页响应
            huiyi_list_resp = self.__getResp(func=self.download_middleware.getResp,
                                             url=self.huiyi_list_url,
                                             mode='POST',
                                             data=huiyi_list_url_data)
            if not huiyi_list_resp:
                LOGGING.info('会议列表页响应获取失败')
                continue

            huiyi_list_response = huiyi_list_resp.text
            # 获取会议url
            huiyi_url_list = self.server.getHuiYiUrlList(resp=huiyi_list_response)
            for huiyi_url in huiyi_url_list:
                save_data = {}
                sha = hashlib.sha1(huiyi_url.encode('utf-8')).hexdigest()
                save_data['sha'] = sha
                save_data['url'] = huiyi_url
                save_data['jibie'] = task_jibie
                save_data['wenji'] = task_url

                # 保存会议种子数据
                self.dao.saveHuiYiUrlData(table=config.LUNWEN_URL_TABLE,
                                          data=save_data,
                                          data_type='huiyi',
                                          create_at=timeutils.getNowDatetime())


def process_start1():
    main = TaskMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


def process_start2():
    main = SpiderMain()
    try:
        main.begin()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start1()
    po = Pool(1)
    for i in range(1):
        po.apply_async(func=process_start2)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
