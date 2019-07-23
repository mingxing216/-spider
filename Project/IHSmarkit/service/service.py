# -*-coding:utf-8-*-

'''

'''
import sys
import os
import requests
from scrapy.selector import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getTitle(self, resp):
        '''This is demo'''
        selector = Selector(text=resp)
        title = selector.xpath("//title/text()").extract_first()

        return title

    # 获取发布单位列表url
    def getPublishUrlList(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取所有发布单位所在的a标签的url
            url_list = selector.xpath("//h1[contains(text(), 'Browse Publishers')]/../../../tr[4]/td/table/tr/td/a[@href]/@href").extract()
            # 遍历每个发布单位url，添加到列表中
            for i in url_list:
                return_list.append(i)
        except Exception:
            return return_list

        return return_list

    # 获取列表页url
    def getCatalogUrl(self, resp):
        selector = Selector(text=resp)
        try:
            # 获取列表页所在的a标签的url
            url = selector.xpath("//ul[@id='upsell-links-ul']/li/a[contains(text(), 'Browse Collection')]/@href").extract_first()
        except Exception:
            url = ''

        return url

    # 获取详情url
    def getDetailUrl(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页所有详情url
            url_list = selector.xpath("//a[@class='document-name']/@href").extract()
            # 遍历每个详情url，存入列表
            for url in url_list:
                return_list.append({'url':url})
        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            next_page = selector.xpath("//a[contains(text(), 'Next Page')]/@href").extract_first()
        except:
            next_page = None

        return next_page






