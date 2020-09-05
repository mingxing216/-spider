# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import json
import requests
import time
import traceback
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from Project.ZheXueSheHuiKeXueQiKan.main.qikanlunwen import data_zhexueshehuikexue

log_file_dir = 'SheHuiKeXue'  # LOG日志存放路径
LOGNAME = '<国家哲学社会科学_期刊_task>'  # LOG名
NAME = '国家哲学社会科学_期刊_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口页url
        self.index_url = 'http://www.nssd.org/journal/fund.aspx'
        self.total_url = 'http://www.nssd.org/journal/record.aspx'
        self.s = None
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def getTotalJournal(self):
        '''
        获取期刊名录中所有期刊，并存入mysql数据库
        '''
        total_resp = self.__getResp(url=self.total_url, method='GET')
        if not total_resp:
            LOGGING.error('入口页面响应获取失败, url: {}'.format(self.total_url))
            return

        total_text = total_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)

        # 获取期刊名录总页数
        journal_pages = self.server.getTotalPage(text=total_text)
        # print(journal_pages)
        # 期刊名录列表页翻页
        for i in range(1, int(journal_pages)+1):
            url = self.total_url + '?p={}'.format(i)
            # 请求响应
            journal_resp = self.__getResp(url=url, method='GET')
            if not journal_resp:
                LOGGING.error('期刊名录第{}页响应失败, url: {}'.format(i, url))
                return
            journal_text = journal_resp.text
            # 获取期刊种子
            journal_list = self.server.getJournalList(text=journal_text)
            # print(journal_list)
            # 存入mysql数据库
            for url in journal_list:
                # 保存url
                self.num += 1
                LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                # 存入数据库
                self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=url, ws='国家哲学社会科学', es='期刊')

    def getCatalog(self):
        '''
        获取学科分类列表页，并进入队列
        '''
        # 访问入口页
        # self.s = requests.session()
        index_resp = self.__getResp(url=self.index_url, method='GET')
        if not index_resp:
            LOGGING.error('入口页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)

        # 获取学科分类种子及名称
        catalog_list = self.server.getCatalogList(text=index_text)
        # print(catalog_list)
        # 列表页进入队列
        self.dao.QueueJobTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=catalog_list)

    def getProfile(self, text, xuekeleibie):
        # 提取期刊详情页种子
        url_list = self.server.getQiKanDetailUrl(text=text, xuekeleibie=xuekeleibie)
        # print(url_list)
        for url in url_list:
            # 保存url
            self.num += 1
            LOGGING.info('当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=url, ws='国家哲学社会科学', es='期刊')

    def run(self):
        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG,
                                             count=1,
                                             lockname=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG_LOCK)
            # print(category_list)
            if category_list:
                for category in category_list:
                    # 数据类型转换
                    task = json.loads(category)
                    # print(task)
                    qikan_url = task['url']
                    xuekefenlei = task['s_xuekefenlei']
                    # 获取期刊列表页
                    catalog_resp = self.__getResp(url=qikan_url, method='GET')
                    if not catalog_resp:
                        LOGGING.error('期刊列表页首页响应失败, url: {}'.format(qikan_url))
                        # 队列一条任务
                        self.dao.QueueOneTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                        break
                    # 获取当前列表总页数
                    total_pages = self.server.getTotalPage(text=catalog_resp.text)
                    # print(total_pages)

                    # 遍历期刊列表页，获取详情页url
                    for i in range(1, int(total_pages)+1):
                        current_url = re.sub(r"\?p=\d+", "?p={}".format(i), qikan_url)
                        # 获取列表页
                        catalog_resp = self.__getResp(url=current_url, method='GET')
                        if not catalog_resp:
                            LOGGING.error('第{}页期刊列表页响应失败, url: {}'.format(i, current_url))
                            # 队列一条任务
                            task['url'] = current_url
                            self.dao.QueueOneTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_CATALOG, data=task)
                            break

                        catalog_text = catalog_resp.text
                        LOGGING.info('已翻到第{}页'.format(i))
                        # 获取详情url
                        self.getProfile(text=catalog_text, xuekeleibie=xuekefenlei)

                    else:
                        LOGGING.info('已翻到最后一页')

            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

    def start(self):
        # # 创建gevent协程
        # g_list = []
        # for category in category_list:
        #     s = gevent.spawn(self.run, category)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        threadpool = ThreadPool(processes=4)
        for i in range(4):
            threadpool.apply_async(func=self.run)

        threadpool.close()
        threadpool.join()

def process_start():
    main = SpiderMain()
    try:
        main.getTotalJournal()
        main.getCatalog()
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' %(end_time - begin_time))
