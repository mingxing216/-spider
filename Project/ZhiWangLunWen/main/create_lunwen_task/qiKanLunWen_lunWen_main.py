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

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<期刊论文_论文任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

manage = multiprocessing.Manager()
TASK_Q = manage.Queue()


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.QiKanLunWen_LunWenTaskDownloader(logging=LOGGING,
                                                                                        proxy_type=config.PROXY_TYPE,
                                                                                        timeout=config.TIMEOUT,
                                                                                        proxy_country=config.COUNTRY)
        self.server = service.QiKanLunWen_LunWenTaskServer(logging=LOGGING)
        self.dao = dao.QiKanLunWen_LunWenTaskDao(logging=LOGGING)


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
        # 初始化期刊时间列表种子模板
        self.qiKan_time_list_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunLun_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'

    def start(self):
        while 1:
            task = TASK_Q.get_nowait()
            task_data = json.loads(task['memo'])
            qiKanUrl = task_data['url']
            xueKeLeiBie = task_data['column_name']

            # 生成单个知网期刊的时间列表种子
            qiKanTimeListUrl, pcode, pykm = self.server.qiKanTimeListUrl(qiKanUrl, self.qiKan_time_list_url_template)
            # 获取期刊时间列表页html源码
            qikanTimeListHtml = self.download_middleware.getResp(url=qiKanTimeListUrl, mode='get')
            if qikanTimeListHtml['status'] == 0:
                # 获取期刊【年】、【期】列表
                qiKanTimeList = self.server.getQiKanTimeList(qikanTimeListHtml)
                if qiKanTimeList:
                    # 循环获取指定年、期页文章列表页种子
                    for qikan_year in qiKanTimeList:
                        # 获取文章列表页种子
                        articleListUrl = self.server.getArticleListUrl(url=self.lunLun_url_template,
                                                                       data=qikan_year,
                                                                       pcode=pcode,
                                                                       pykm=pykm)
                        for articleUrl in articleListUrl:
                            # 获取论文列表页html源码
                            article_list_html = self.download_middleware.getResp(url=articleUrl, mode='get')
                            if article_list_html['status'] == 0:
                                # 获取论文种子列表
                                article_url_list = self.server.getArticleUrlList(article_list_html, qiKanUrl,
                                                                                 xueKeLeiBie)
                                if article_url_list:
                                    for article_url in article_url_list:
                                        # 存储种子
                                        self.dao.saveProjectUrlToMysql(memo=article_url)
                                        # print(article_url)
                                else:
                                    LOGGING.error('论文种子列表获取失败')
                            else:
                                LOGGING.error('论文列表页html源码获取失败')
                else:
                    LOGGING.error('年、期列表获取失败。')
            else:
                LOGGING.error('期刊时间列表页获取失败。')

            LOGGING.info('剩余任务数: {}'.format(TASK_Q.qsize()))
            time.sleep(10)




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
