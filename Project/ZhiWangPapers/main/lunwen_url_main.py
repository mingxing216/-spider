# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import multiprocessing
import ast

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangPapers.middleware import download_middleware
from Project.ZhiWangPapers.service import service
from Project.ZhiWangPapers.dao import dao
from Project.ZhiWangPapers import config

log_file_dir = 'ZhiWangPapers'  # LOG日志存放路径
LOGNAME = '<知网期刊论文数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.LunWenDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.LunWenServer(logging=LOGGING)
        self.dao = dao.LunWenDao(logging=LOGGING)


class CreateLunWenQueueMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化第一根栏目redis集合名
        self.one_set_name = 'article_qikan_queue_1'
        # 初始化第七根栏目redis集合名
        self.seven_set_name = 'article_qikan_queue_2'
        # 初始化redis数据库分布式锁名
        self.redis_lockname = 'zhiwang_article_lock'
        # 初始化期刊时间列表种子模板
        self.qiKan_time_list_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunLun_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'
        # 初始化mysql数据库论文任务表名
        self.lunwen_url_table = 'ss_paper_url'


    # 任务处理阶段
    def task_processing(self, qikan_url_data):
        url_data = ast.literal_eval(qikan_url_data)
        qiKanUrl = url_data['url']
        xueKeLeiBie = url_data['column_name']

        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrl, pcode, pykm = self.server.qiKanTimeListUrl(qiKanUrl, self.qiKan_time_list_url_template)
        # 获取期刊时间列表页html源码
        qikanTimeListHtml = self.download_middleware.getResp(url=qiKanTimeListUrl)
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
                        article_list_html = self.download_middleware.getResp(url=articleUrl)
                        if article_list_html['status'] == 0:
                            # 获取论文种子列表
                            article_url_list = self.server.getArticleUrlList(article_list_html, qiKanUrl, xueKeLeiBie)
                            if article_url_list:
                                for article_url in article_url_list:
                                    # 存储种子
                                    self.dao.saveProjectUrlToMysql(table=self.lunwen_url_table, url_data=article_url)

                            else:
                                LOGGING.error('论文种子列表获取失败')
                        else:
                            LOGGING.error('论文列表页html源码获取失败')
            else:
                LOGGING.error('年、期列表获取失败。')
        else:
            LOGGING.error('期刊时间列表页获取失败。')

    # 准备阶段
    def begin(self):
        while 1:
            # 从redis获取期刊任务
            qikan_url_data = self.dao.getQiKanUrlData(key=self.one_set_name, lockname=self.redis_lockname)
            # 如果任务获取成功
            if qikan_url_data:
                # 任务处理
                self.task_processing(qikan_url_data=qikan_url_data)

            # 如果任务获取失败
            else:
                # 从redis获取期刊任务
                qikan_url_data = self.dao.getQiKanUrlData(key=self.seven_set_name, lockname=self.redis_lockname)
                # 如果任务获取成功
                if qikan_url_data:
                    # 任务处理
                    self.task_processing(qikan_url_data=qikan_url_data)
                # 如果任务获取失败
                else:
                    LOGGING.error('redis队列空！！！600秒后重新尝试获取')
                    time.sleep(600)
                    continue



if __name__ == '__main__':
    begin_time = time.time()
    main = CreateLunWenQueueMain()
    main.begin()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
