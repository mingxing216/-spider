# -*-coding:utf-8-*-

'''
知网期刊任务生成启动文件
'''
import sys
import os
import pprint
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from log import log
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider
from Project.ZhiWangPeriodicalProject.services import zhiwang_periodical_serveice

logname = 'zhiwang_periodical'
logging = log.ILog(logname)


class SpiderMain(object):
    def __init__(self):
        self.index_url = 'http://navi.cnki.net/knavi/Common/LeftNavi/Journal'
        # 用于获取第n个根栏目源码的种子
        self.column_url = 'http://navi.cnki.net/knavi/Common/ClickNavi/Journal'
        # 期刊列表页url
        self.column_list_url = 'http://navi.cnki.net/knavi/Common/Search/Journal'
        # 每页显示数量
        self.pagecount = 21

    # 翻页
    def next_page(self, url, data, page_number, spider, server, column_name, redis_name, redis_name2):
        '''
        翻页抓取
        :param url: 列表页url
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
                for i in range(10):
                    # 获取列表页html源码
                    column_list_html = spider.getRespForPost(url=self.column_list_url, data=data)
                    if len(column_list_html) < 300:
                        continue
                    else:
                        # 生成期刊主页任务队列
                        server.createTaskQueue(column_list_html, column_name, redis_name, redis_name2)

    def run(self):
        # 模块对象
        spider = zhiwang_periodical_spider.SpiderMain()
        server = zhiwang_periodical_serveice.zhiwangPeriodocalService()
        # 获取首页源码
        index_url_data = {
            'productcode': 'CJFD',
            'index': 1
        }
        index_html = spider.getRespForPost(url=self.index_url, data=index_url_data)
        if index_html is not None:
            # 获取根栏目数量
            column_numbers = server.getColumnNumber(index_html)
            i = 0
            for column_number in range(column_numbers):
                i += 1
                if i == 1 or i == column_numbers: # 只获取第一个根栏目和最后一个根栏目的数据
                    # 获取第column_number个根栏目源码
                    column_url_data = {
                        'productcode': 'CJFD',
                        'ClickIndex': column_number + 1
                    }
                    for i in range(10):
                        column_html = spider.getRespForPost(url=self.column_url, data=column_url_data)
                        if len(column_html) > 400:
                            # 获取当前栏目下所有子栏目请求参数
                            request_datas = server.getColumnSunData(column_html)
                            for request_data in request_datas:
                                if request_data['has_next'] is True:
                                    # 生成请求参数
                                    searchstatejson = ('{"StateID":"","Platfrom":"","QueryTime":"","Account":"knavi",'
                                                       '"ClientToken":"","Language":"","CNode":{"PCode":"CJFD","SMode":"",'
                                                       '"OperateT":""},"QNode":{"SelectT":"","Select_Fields":"","S_DBCodes":"",'
                                                       '"QGroup":[{"Key":"Navi","Logic":1,"Items":[],'
                                                       '"ChildItems":[{"Key":"Journal","Logic":1,"Items":[{"Key":1,"Title":"",'
                                                       '"Logic":1,"Name":"%s","Operate":"","Value":"%s?","ExtendType":0,'
                                                       '"ExtendValue":"","Value2":""}],"ChildItems":[]}]}],"OrderBy":"OTA|DESC",'
                                                       '"GroupBy":"","Additon":""}}' % (request_data['name'], request_data['value']))
                                    column_list_url_data = {
                                        'SearchStateJson': searchstatejson,
                                        # 'displaymode': 1,
                                        'pageindex': 1, # 当前页数
                                        'pagecount': self.pagecount, # 每页显示数量
                                        # 'index': 1
                                    }
                                    # 获取列表页html源码
                                    column_list_html = spider.getRespForPost(url=self.column_list_url, data=column_list_url_data)
                                    if column_list_html is not None:
                                        if i == 1: # 第一个栏目的存法
                                            # 抓取文章用的期刊队列
                                            redis_key1 = 'article_qikan_queue_1'
                                            # 抓取期刊用的期刊队列
                                            redis_key2 = 'qikan_queue_1'
                                            # 生成期刊主页任务队列， 获取总期刊数
                                            qikan_number = server.createTaskQueue(column_list_html,
                                                                                  request_data['column_name'],
                                                                                  redis_key1, redis_key2)
                                            # 生成总页数
                                            page_number = int(qikan_number) / int(self.pagecount)
                                            if page_number > int(page_number):
                                                page_number = int(page_number) + 1
                                                # 翻页抓取
                                                self.next_page(self.column_list_url, column_list_url_data, page_number,
                                                               spider, server, request_data['column_name'],
                                                               redis_key1, redis_key2)
                                            else:
                                                page_number = int(page_number)
                                                # 翻页抓取
                                                self.next_page(self.column_list_url, column_list_url_data, page_number,
                                                               spider, server, request_data['column_name'],
                                                               redis_key1, redis_key2)
                                        if i == column_numbers: # 最后一个栏目的存法
                                            # 抓取文章用的期刊队列
                                            redis_key1 = 'article_qikan_queue_2'
                                            # 抓取期刊用的期刊队列
                                            redis_key2 = 'qikan_queue_2'
                                            # 生成期刊主页任务队列， 获取总期刊数
                                            qikan_number = server.createTaskQueue(column_list_html,
                                                                                  request_data['column_name'],
                                                                                  redis_key1, redis_key2)
                                            # 生成总页数
                                            page_number = int(qikan_number) / int(self.pagecount)
                                            if page_number > int(page_number):
                                                page_number = int(page_number) + 1
                                                # 翻页抓取
                                                self.next_page(self.column_list_url, column_list_url_data, page_number,
                                                               spider, server, request_data['column_name'],
                                                               redis_key1, redis_key2)
                                            else:
                                                page_number = int(page_number)
                                                # 翻页抓取
                                                self.next_page(self.column_list_url, column_list_url_data, page_number,
                                                               spider, server, request_data['column_name'],
                                                               redis_key1, redis_key2)

                        else:

                            #     break

                            # break


if __name__ == '__main__':
    main = SpiderMain()
    begin_time = time.time()
    main.run()
    print(time.time() - begin_time)