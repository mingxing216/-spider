# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import json
import hashlib
import traceback
import multiprocessing
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<会议论文_论文任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

manage = multiprocessing.Manager()
TASK_Q = manage.Queue()


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.HuiYiLunWen_LunWenTaskDownloader(logging=LOGGING,
                                                                                        update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                                        proxy_type=config.PROXY_TYPE,
                                                                                        timeout=config.TIMEOUT,
                                                                                        retry=config.RETRY,
                                                                                        proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_LunWenTaskServer(logging=LOGGING)
        self.dao = dao.HuiYiLunWen_LunWenTaskDao(logging=LOGGING)


class TaskMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        LOGGING.info('准备生成任务队列...')
        task_list = self.dao.getTask()
        for task in task_list:
            TASK_Q.put(task)
        LOGGING.info('任务队列已生成，任务数: {}'.format(TASK_Q.qsize()))


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化会议列表页url
        self.huiyi_list_url = 'http://navi.cnki.net/knavi/DpaperDetail/GetDpaperListinPage'

    def start(self):
        while 1:
            task = TASK_Q.get_nowait()
            task_data = json.loads(task['memo'])
            task_url = task_data['url']
            task_jibie = task_data['jibie']

            # 获取pcode、lwjcode
            pcode, lwjcode = self.server.getPcodeAndLwjcode(data=task_url)

            # 生成会议数量页url
            huiyi_number_url = self.server.getHuiYiNumberUrl(pcode=pcode, lwjcode=lwjcode)

            # 获取会议数量页html
            huiyi_number_resp = self.download_middleware.getResp(url=huiyi_number_url, mode='get')
            if huiyi_number_resp['status'] == 0:
                huiyi_number_response = huiyi_number_resp['data'].content.decode('utf-8')
                # 获取会议数量
                huiyi_number = self.server.getHuiYiNumber(resp=huiyi_number_response)
                if huiyi_number > 0:
                    # 生成总页数
                    page_number = self.server.getPageNumber(huiyi_number=huiyi_number)
                    for page in range(page_number):
                        # 生成会议列表页请求参数
                        huiyi_list_url_data = self.server.getHuiYiListUrlData(pcode=pcode, lwjcode=lwjcode, page=page)
                        # 获取会议列表页响应
                        huiyi_list_resp = self.download_middleware.getResp(url=self.huiyi_list_url,
                                                                           mode='post',
                                                                           data=huiyi_list_url_data)
                        if huiyi_list_resp['status'] == 0:
                            huiyi_list_response = huiyi_list_resp['data'].content.decode('utf-8')

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
                                self.dao.saveHuiYiUrlData(memo=save_data, sha=sha)

                        else:
                            LOGGING.error('会议列表页响应获取失败，url: {}, data: {}'.format(self.huiyi_list_url, huiyi_list_url_data))
                else:
                    LOGGING.warning('会议总数量未获取到 或 等于0，url: {}'.format(huiyi_number_url))
            else:
                LOGGING.error('会议数量页html获取失败，url: {}'.format(huiyi_number_url))
                continue


def process_start1():
    main = TaskMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


def process_start2():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start1()
    po = Pool(config.HUIYILUNWEN_LUNWENRENWU_PROCESS_NUMBER)
    for i in range(config.HUIYILUNWEN_LUNWENRENWU_PROCESS_NUMBER):
        po.apply_async(func=process_start2)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
