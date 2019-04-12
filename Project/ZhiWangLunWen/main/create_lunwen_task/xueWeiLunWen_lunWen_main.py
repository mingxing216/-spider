# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import json
import traceback
import multiprocessing
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<学位论文_论文任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

manage = multiprocessing.Manager()
TASK_Q = manage.Queue()


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.XueWeiLunWen_LunWenTaskDownloader(logging=LOGGING,
                                                                                         proxy_type=config.PROXY_TYPE,
                                                                                         timeout=config.TIMEOUT,
                                                                                         proxy_country=config.COUNTRY)
        self.server = service.XueWeiLunWen_LunWenTaskServer(logging=LOGGING)
        self.dao = dao.XueWeiLunWen_LunWenTaskDao(logging=LOGGING)


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
        # 总页数url
        self.page_number_url = 'http://navi.cnki.net/knavi/PPaperDetail/GetArticleBySubject'
        # 论文获取url
        self.lunwen_list_url = 'http://navi.cnki.net/knavi/PPaperDetail/GetArticleBySubjectinPage'

    def handle(self, task, page, zhuanye, zhuanye_id):
        # 获取列表页请求参数
        data = self.server.getLunWenPageData2(task, page, zhuanye_id)
        # 获取列表页响应
        lunwen_list_resp = self.download_middleware.getResp(url=self.lunwen_list_url, mode='post', data=data)
        if lunwen_list_resp['status'] == 0:
            lunwen_list_resp = lunwen_list_resp['data'].content.decode('utf-8')
            # 获取论文队列参数
            lunwen_url_list = self.server.getLunWenUrlList(resp=lunwen_list_resp, zhuanye=zhuanye)
            for lunwen_url_data in lunwen_url_list:
                # 保存数据
                self.dao.saveLunWenUrlData(memo=lunwen_url_data)

        else:
            LOGGING.warning('论文列表页响应获取失败，url: {}, data: {}'.format(self.lunwen_list_url, data))

    def start(self):
        while 1:
            # 获取任务
            task = TASK_Q.get_nowait()
            task_data = json.loads(task['memo'])
            task_url = task_data['url']
            # 生成专业列表页url
            zhuanye_url = self.server.getZhuanYePageData(data=task_url)
            # 获取专业列表页响应
            zhuanye_resp = self.download_middleware.getResp(url=zhuanye_url, mode='get')
            if zhuanye_resp['status'] == 0:
                zhuanye_resp = zhuanye_resp['data'].content.decode('utf-8')
                # 获取专业列表
                zhuanye_list = self.server.getZhuanYeList(resp=zhuanye_resp)
                for zhuanye in zhuanye_list:
                    # 获取总页数页参数
                    zhuanye_req_data = self.server.getZhuanYeReqData(task=task_url, data=zhuanye)
                    # 获取总页数页响应
                    zhuanye_resp = self.download_middleware.getResp(url=self.page_number_url, mode='post', data=zhuanye_req_data)
                    if zhuanye_resp['status'] == 0:
                        page_number_resp = zhuanye_resp['data'].content.decode('utf-8')
                        page_number = self.server.getPageNumber(resp=page_number_resp)

                        threadpool = ThreadPool()
                        for page in range(int(page_number)):
                            threadpool.apply_async(func=self.handle, args=(task_url, page, zhuanye['zhuanYe'], zhuanye['zhuanYeId']))
                            # break
                        threadpool.close()
                        threadpool.join()

                    else:
                        LOGGING.error('总页数页响应失败，url: {}, data: {}'.format(self.page_number_url, zhuanye_req_data))
                    # break
            else:
                LOGGING.error('专业列表页获取失败，url: {}'.format(zhuanye_url))


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
    po = Pool(config.XUEWEILUNWEN_LUNWENRENWU_PROCESS_NUMBER)
    for i in range(config.XUEWEILUNWEN_LUNWENRENWU_PROCESS_NUMBER):
        po.apply_async(func=process_start2)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
