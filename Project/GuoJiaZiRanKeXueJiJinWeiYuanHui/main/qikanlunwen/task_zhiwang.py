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
import hashlib
import random
import traceback
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config

log_file_dir = 'ZiRanKeXue'  # LOG日志存放路径
LOGNAME = '<搜索知网_论文_task>'  # LOG名
NAME = '搜索知网_论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口页url
        self.result_url = 'https://kns.cnki.net/kns/brief/default_result.aspx'
        self.SearchHandler_url = 'https://kns.cnki.net/kns/request/SearchHandler.ashx'
        self.base_url = 'https://search.cnki.net/sug/su.ashx?action=getsmarttips&kw={title}&t=%E7%AF%87%E5%90%8D&dbt=SCDB&attr=1&p={random}&td={tt}'
        self.s = requests.Session()
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码, url: {}'.format(url))
                    continue
                elif '对不起，服务器上不存在此用户！' in resp.text:
                    LOGGING.error('对不起，服务器上不存在此用户！ url: {}'.format(url))
                    continue

            return resp

        else:
            # LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def getNextProfile(self, next_page, task):
        while next_page:
            # 获取列表页
            catalog_resp = self.__getResp(url=url, method='GET', s=self.s)
            print(self.s.cookies)
            if not catalog_resp:
                LOGGING.error('列表页响应失败, url: {}'.format(url))
                # 逻辑删除任务
                self.dao.delete_logic_task_from_mysql(table=config.MYSQL_TEST, sha=sha)
                return

            catalog_resp.encoding = catalog_resp.apparent_encoding
            catalog_text = catalog_resp.text
            # 遍历结果，分别判断标题、第一作者、来源是否一致
            for data in self.server.getResults(catalog_text):
                print(data)
                # 获取附加信息中第一作者
                authors = task.get('authors').replace('；', ';').split(';')
                if task.get('chineseTitle') == data['title'] and authors[0] == data['author'] and task.get('journal') == data['source']:
                    LOGGING.info('正确匹配结果, url: {}, title: {}'.format(task.get('url'), task.get('chineseTitle')))
                else:
                    LOGGING.error('无匹配结果, url: {}, title: {}'.format(task.get('url'), task.get('chineseTitle')))

            # 判断是否有下一页
            next_page = self.server.nextPage(catalog_text)

    def getProfile(self, text, task):
        # 判断列表页是否有结果
        result = self.server.getResult(text)
        # print(result)
        if result:
            LOGGING.info('找到 {} 条结果, url: {}, title: {}'.format(str(result), task.get('url'), task.get('chineseTitle')))
            # 遍历结果，分别判断标题、第一作者、来源是否一致
            for data in self.server.getResults(text):
                # print(data)
                # 获取附加信息中第一作者
                authors = task.get('authors').replace('；', ';').split(';')
                if task.get('chineseTitle') == data['title'] and authors[0] == data['author'] and task.get('journal') == data['source']:
                    LOGGING.info('正确匹配结果, url: {}, title: {}'.format(task.get('url'), task.get('chineseTitle')))
                    # 存储到mysql数据库
                    # task['url'] = data['url']
                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=task, ws='中国知网', es='论文_profile')
                    break
            else:
                LOGGING.error('无匹配结果, url: {}, title: {}'.format(task.get('url'), task.get('chineseTitle')))
                # # 存储到mysql数据库
                # task['url'] = data['url']
                # self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=task, ws='中国知网', es='论文_profile')

            # # 判断是否有下一页
            # next_page = self.server.nextPage(text)
            # print(next_page)
            # self.getNextProfile(next_page=next_page, task=task)


        else:
            LOGGING.error('无结果, url: {}, title: {}'.format(task.get('url'), task.get('chineseTitle')))
        # # 提取详情页种子
        # next_urls = self.server.getDetailUrl(json=json, xuekeleibie=xuekeleibie)
        # # print(next_urls)
        # for url in next_urls:
        #     # 保存url
        #     self.num += 1
        #     LOGGING.info('当前已抓种子数量: {}'.format(self.num))
        #     # 存入数据库
        #     self.dao.saveTaskToMysql(table=config.MYSQL_TEST, memo=url, ws='中国知网', es='论文_catalog')

    def run(self, category):
        # 数据类型转换
        task = self.server.getEvalResponse(category)
        # print(task)
        url = task['url'] + '(FFD%2c%27RANK%27)+desc&queryid=0'
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        title = task['chineseTitle']
        authors = task['authors']
        journal = task['journal']

        # POST参数
        data = {
            'txt_1_sel': 'SU$%=|',
            'txt_1_value1': title,
            'txt_1_special1': '%',
            'txt_extension': '',
            'currentid': 'txt_1_value1',
            'dbJson': 'coreJson',
            'dbPrefix': 'SCDB',
            'db_opt': 'CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
            'singleDB': 'SCDB',
            'db_codes': 'CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
            'singleDBName': '',
            'againConfigJson': 'false',
            'action': 'scdbsearch',
            'ua': 1.11
        }

        # 建立会话，获取cookie
        result_resp = self.__getResp(url=self.result_url, method='POST', s=self.s, data=data)
        # print(self.s.cookies)
        if not result_resp:
            LOGGING.error('会话页响应失败, url: {}'.format(self.result_url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_TEST, sha=sha)
            return

        # POST参数
        data1 = {
            'action': '',
            'ua': 1.11,
            'formDefaultResult': '',
            'isinEn': 1,
            'PageName': 'ASP.brief_default_result_aspx',
            'DbPrefix': 'SCDB',
            'DbCatalog': '中国学术文献网络出版总库',
            'ConfigFile': 'SCDBINDEX.xml',
            'db_opt': 'CJFQ,CDFD,CMFD,CPFD,IPFD,CCND,CCJD',
            'txt_1_sel': 'TI$%=|',
            'txt_1_value1': title,
            'txt_1_special1': '%',
            'his': 0,
            'parentdb': 'SCDB'
        }

        # 补充cookie
        Search_resp = self.__getResp(url=self.SearchHandler_url, method='POST', s=self.s, data=data1)
        # print(self.s.cookies)
        if not Search_resp:
            LOGGING.error('会话页响应失败, url: {}'.format(self.SearchHandler_url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_TEST, sha=sha)
            return

        # # 获取标题输入url
        # t = round(time.time() * 1000)
        # title_url = self.base_url.format(title=title, random=random.random(), tt=t)
        # print(title_url)
        # title_resp = self.__getResp(url=title_url, method='GET', s=self.s)
        # print(self.s.cookies)
        # if not title_resp:
        #     LOGGING.error('标题搜索页响应失败, url: {}'.format(title_url))
        #     # 逻辑删除任务
        #     self.dao.deleteLogicTask(table=config.MYSQL_TEST, sha=sha)
        #     return

        # 获取列表页
        catalog_resp = self.__getResp(url=url, method='GET', s=self.s)
        # print(self.s.cookies)
        if not catalog_resp:
            LOGGING.error('列表页响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_TEST, sha=sha)
            return

        catalog_resp.encoding = catalog_resp.apparent_encoding
        catalog_text = catalog_resp.text
        # with open('catalog.txt', 'w')as f:
        #     f.write(catalog_text)

        # 获取详情页
        self.getProfile(text=catalog_text, task=task)


    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.get_task_from_redis(key=config.REDIS_ZHIWANG_TEST,
                                                         count=1,
                                                         lockname=config.REDIS_ZHIWANG_TEST_LOCK)
            # print(category_list)
            LOGGING.info('获取{}个任务'.format(len(category_list)))

            if category_list:
                # # 创建gevent协程
                # g_list = []
                # for category in category_list:
                #     s = gevent.spawn(self.run, category)
                #     g_list.append(s)
                # gevent.joinall(g_list)

                # 创建线程池
                threadpool = ThreadPool()
                for category in category_list:
                    threadpool.apply_async(func=self.run, args=(category,))

                threadpool.close()
                threadpool.join()

                # time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return


def process_start():
    main = SpiderMain()
    try:
        # main.getCatalog()
        main.start()
        # main.run("{'achievementID': '1000013504304', 'authors': 'Qingyun Liu;Hangyue Zhou;Jiqin Zhu;Yanting Yang;Xiaodong Liu;Dongmei Wang;Xiaomei Zhang;Linhai Zhuo', 'chineseTitle': 'Self-assembly into temperature dependent micro-/nano-aggregates of 5,10,15,20-tetrakis(4-carboxyl phenyl)-porphyrin', 'conference': '', 'doi': '10.1016/j.msec.2013.08.015', 'doiUrl': 'https://doi.org/10.1016/j.msec.2013.08.015', 'downloadHref': '', 'enAbstract': '', 'enKeyword': '', 'englishTitle': 'Self-assembly into temperature dependent micro-/nano-aggregates of 5,10,15,20-tetrakis(4-carboxyl phenyl)-porphyrin', 'fieldCode': 'B010503', 'fulltext': '1000013504304', 'fundProject': '卟啉酞菁功能配合物-无机纳米复合体的组装及在比色生物传感中的应用', 'fundProjectCode': '831268', 'fundProjectNo': '21271119', 'id': '9150d76a-fd84-46f3-802e-87c9dd167df1', 'journal': 'Materials Science and Engineering: C', 'organization': '山东科技大学', 'organizationID': '100145', 'outputSubIrSource': '', 'pageRange': '', 'productType': '4', 'publishDate': '2013', 'source': 'origin', 'supportType': '218', 'supportTypeName': '面上项目', 'year': '2013', 'zhAbstract': '', 'zhKeyword': '', 'xueKeLeiBie': '化学科学部', 'url': 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_default_result_aspx&isinEn=1&dbPrefix=SCDB&dbCatalog=%e4%b8%ad%e5%9b%bd%e5%ad%a6%e6%9c%af%e6%96%87%e7%8c%ae%e7%bd%91%e7%bb%9c%e5%87%ba%e7%89%88%e6%80%bb%e5%ba%93&ConfigFile=SCDBINDEX.xml&research=off&t=1591352870831&keyValue=Self-assembly%20into%20temperature%20dependent%20micro-/nano-aggregates%20of%205%2C10%2C15%2C20-tetrakis%284-carboxyl%20phenyl%29-porphyrin&S=1&sorttype=', 'pdfUrl': 'http://ir.nsfc.gov.cn/paperDownload/1000013504304.pdf'}")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' %(end_time - begin_time))
