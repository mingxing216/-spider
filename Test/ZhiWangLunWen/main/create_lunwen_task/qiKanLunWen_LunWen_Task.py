# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import json
import multiprocessing
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import timeutils
from Test.ZhiWangLunWen.middleware import download_middleware
from Test.ZhiWangLunWen.service import service
from Test.ZhiWangLunWen.dao import dao
from Test.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_期刊论文_task>'  # LOG名
NAME = '知网_期刊论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量

manage = multiprocessing.Manager()
TASK_Q = manage.Queue()


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.QiKanLunWen_LunWenTaskServer(logging=LOGGING)
        self.dao = dao.QiKanLunWen_LunWenTaskDao(logging=LOGGING,
                                                 mysqlpool_number=config.MYSQL_POOL_NUMBER,
                                                 redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class TaskMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def start(self):
        LOGGING.info('准备生成任务队列...')
        task_list = self.dao.getQiKanTask(table=config.QIKAN_URL_TABLE, data_type='qikan')
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
        try:
            task_data = json.loads(task['memo'])
        except Exception as e:
            task_data = None

        if not task_data:
            LOGGING.info('任务数据提取失败')
            return

        qiKanUrl = task_data['url']
        xueKeLeiBie = task_data['column_name']
        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrlData = self.server.qiKanTimeListUrl(qiKanUrl, self.qiKan_time_list_url_template)
        if not qiKanTimeListUrlData:
            LOGGING.info('知网期刊的时间列表种子获取失败')
            return

        qiKanTimeListUrl = qiKanTimeListUrlData['qiKanTimeListUrl']
        pcode = qiKanTimeListUrlData['pcode']
        pykm = qiKanTimeListUrlData['pykm']

        # 获取期刊时间列表页html源码
        qikanTimeListResp = self.__getResp(func=self.download_middleware.getResp,
                                           url=qiKanTimeListUrl,
                                           mode='GET')
        if not qikanTimeListResp:
            LOGGING.info('期刊时间列表页响应获取失败')
            return

        qikanTimeListResponse = qikanTimeListResp.text
        # 获取期刊【年】、【期】列表
        qiKanTimeList = self.server.getQiKanTimeList(qikanTimeListResponse)
        # 循环获取指定年、期页文章列表页种子
        for qikan_year in qiKanTimeList:
            # 获取文章列表页种子
            articleListUrl = self.server.getArticleListUrl(url=self.lunLun_url_template,
                                                           data=qikan_year,
                                                           pcode=pcode,
                                                           pykm=pykm)

            for articleUrl in articleListUrl:
                # 获取论文列表页html源码
                article_list_resp = self.__getResp(func=self.download_middleware.getResp,
                                                   url=articleUrl,
                                                   mode='GET')
                if not article_list_resp:
                    LOGGING.info('论文列表页响应获取失败')
                    continue

                article_list_response = article_list_resp.text
                # 获取论文种子列表
                article_url_list = self.server.getArticleUrlList(article_list_response, qiKanUrl, xueKeLeiBie)
                for article_url in article_url_list:
                    # 存储种子
                    self.dao.saveLunWenUrlData(table=config.LUNWEN_URL_TABLE,
                                               data=article_url,
                                               data_type='qikan',
                                               create_at=timeutils.get_now_datetime())


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
