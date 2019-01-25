# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangPapers.middleware import download_middleware
from Project.ZhiWangPapers.service import service
from Project.ZhiWangPapers.dao import dao
from Project.ZhiWangPapers import config

log_file_dir = 'ZhiWangPapers'  # LOG日志存放路径
LOGNAME = '<知网待抓取任务爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.UrlDownloader(logging=LOGGING,
                                                                     update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                     proxy_type=config.PROXY_TYPE,
                                                                     timeout=config.TIMEOUT,
                                                                     retry=config.RETRY,
                                                                     proxy_country=config.COUNTRY)
        self.server = service.UrlServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.index_url = 'http://navi.cnki.net/knavi/Common/LeftNavi/Journal'
        # 用于获取第n个根栏目源码的种子
        self.column_url = 'http://navi.cnki.net/knavi/Common/ClickNavi/Journal'
        # 期刊列表页url
        self.column_list_url = 'http://navi.cnki.net/knavi/Common/Search/Journal'
        # 每页显示数量
        self.pagecount = 21

    # 翻页
    def next_page(self, data, page_number, column_name, redis_name, redis_name2, requests_data):
        '''
        翻页抓取
        :param data: 列表页post请求参数
        :param page_number: 总页数
        :param spider: 爬虫对象
        :param server: 服务层对象
        :column_name: 所属栏目名组合
        :redis_name: 抓取文章用的期刊队列名
        :redis_name2: 抓取期刊用的期刊队列名
        :return:
        '''
        for page in range(page_number + 1):
            if page >= 2:
                data['pageindex'] = page
                # 生成期刊主页任务队列
                # 获取列表页html源码
                column_list_html = self.download_middleware.getResp(url=self.column_list_url, data=data)
                if column_list_html is not None:
                    # 生成期刊主页任务队列
                    self.server.createTaskQueue(column_list_html, column_name, redis_name,
                                                redis_name2, requests_data=requests_data)

    def start(self):
        # 获取首页源码
        index_resp = self.download_middleware.getIndexHtml(url=self.index_url)
        if not index_resp:
            LOGGING.error('首页响应获取失败')

        # 获取根栏目数量
        column_numbers = self.server.getColumnNumber(index_resp)

        i = 0
        for column_number in range(column_numbers):
            i += 1
            if i == 1 or i == column_numbers:  # 只获取第一个根栏目和最后一个根栏目的数据
                # 获取第column_number个根栏目源码
                column_url_data = {
                    'productcode': 'CJFD',
                    'ClickIndex': column_number + 1
                }

                column_resp = self.download_middleware.getResp(url=self.column_url, data=column_url_data)
                if column_resp is not None:
                    # 获取当前栏目下所有子栏目请求参数
                    request_datas = self.server.getColumnSunData(column_resp)
                    lanmu_number = 0
                    for request_data in request_datas:
                        lanmu_number += 1
                        if request_data['has_next'] is True:
                            # 生成请求参数
                            searchstatejson = ('{"StateID":"","Platfrom":"","QueryTime":"","Account":"knavi",'
                                               '"ClientToken":"","Language":"","CNode":{"PCode":"CJFD","SMode":"",'
                                               '"OperateT":""},"QNode":{"SelectT":"","Select_Fields":"","S_DBCodes":"",'
                                               '"QGroup":[{"Key":"Navi","Logic":1,"Items":[],'
                                               '"ChildItems":[{"Key":"Journal","Logic":1,"Items":[{"Key":1,"Title":"",'
                                               '"Logic":1,"Name":"%s","Operate":"","Value":"%s?","ExtendType":0,'
                                               '"ExtendValue":"","Value2":""}],"ChildItems":[]}]}],"OrderBy":"OTA|DESC",'
                                               '"GroupBy":"","Additon":""}}' % (
                                               request_data['name'], request_data['value']))

                            column_list_url_data = {
                                'SearchStateJson': searchstatejson,
                                'displaymode': 1,
                                'pageindex': 1,  # 当前页数
                                'pagecount': self.pagecount,  # 每页显示数量
                                # 'index': 1,
                                'random': random.random()
                            }
                            # 获取列表页html源码
                            column_list_resp = self.download_middleware.getResp(url=self.column_list_url,
                                                                                data=column_list_url_data)

                            if column_list_resp is not None:
                                if i == 1:  # 第一个栏目的存法
                                    # 抓取文章用的期刊队列
                                    redis_key1 = 'article_qikan_queue_1'
                                    # 抓取期刊用的期刊队列
                                    redis_key2 = 'qikan_queue_1'
                                    # 生成期刊主页任务队列， 获取总期刊数
                                    qikan_number = self.server.createTaskQueue(column_list_resp,
                                                                          request_data['column_name'],
                                                                          redis_key1,
                                                                          redis_key2,
                                                                          requests_data=request_data)
                                    # 生成总页数
                                    page_number = int(qikan_number) / int(self.pagecount)
                                    if page_number > int(page_number):
                                        page_number = int(page_number) + 1
                                        # 翻页抓取
                                        self.next_page(column_list_url_data, page_number,
                                                       request_data['column_name'], redis_key1, redis_key2,
                                                       requests_data=request_data)
                                    else:
                                        page_number = int(page_number)
                                        # 翻页抓取
                                        self.next_page(column_list_url_data, page_number,
                                                       request_data['column_name'], redis_key1, redis_key2,
                                                       requests_data=request_data)

                                if i == column_numbers:  # 最后一个栏目的存法
                                    print(1)
                                    # 抓取文章用的期刊队列
                                    redis_key1 = 'article_qikan_queue_2'
                                    # 抓取期刊用的期刊队列
                                    redis_key2 = 'qikan_queue_2'
                                    # 生成期刊主页任务队列， 获取总期刊数
                                    qikan_number = self.server.createTaskQueue(column_list_resp,
                                                                          request_data['column_name'],
                                                                          redis_key1,
                                                                          redis_key2,
                                                                          requests_data=request_data)
                                    # 生成总页数
                                    page_number = int(qikan_number) / int(self.pagecount)
                                    if page_number > int(page_number):
                                        page_number = int(page_number) + 1
                                        # 翻页抓取
                                        self.next_page(column_list_url_data, page_number,
                                                       request_data['column_name'], redis_key1, redis_key2,
                                                       requests_data=request_data)
                                    else:
                                        page_number = int(page_number)
                                        # 翻页抓取
                                        self.next_page(column_list_url_data, page_number,
                                                       request_data['column_name'], redis_key1, redis_key2,
                                                       requests_data=request_data)

            #             break
            # break

if __name__ == '__main__':
    main = SpiderMain()
    main.start()
