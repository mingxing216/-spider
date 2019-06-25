# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
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

    # 获取各学科列表url
    def getSubjectUrlList(self, resp, index_url):
        return_list = []
        selector = Selector(text=resp)
        # 获取所有学科url所在的input标签
        url_list = selector.xpath("//fieldset[@id='disc']/ul/li/input")
        # 获取所有学科名称所在的label标签
        name_list = selector.xpath("//fieldset[@id='disc']/ul/li/label")
        # 遍历所有学科标签，获取每个学科中的name-value属性值,并拼成新的列表url,以及获取学科名称
        for i in range(len(url_list)):
            name = url_list[i].xpath("./@name").extract_first()
            value = url_list[i].xpath("./@value").extract_first()
            subject = re.sub(r'\s*\(.*\)', '', name_list[i].xpath("./span/text()").extract_first())
            url = index_url + '&' + name + '=' + value
            return_list.append({'url':url, 'xueKeLeiBie':subject})

        return return_list

    # 获取详情url
    def getDetailUrl(self, resp, xueke):
        return_list = []
        selector = Selector(text=resp)
        # 获取一页所有详情url
        url_list = selector.xpath("//div[@class='title']/h3/a/@href").extract()
        # 遍历每个详情url，加上域名，拼接成完整的url
        for url in url_list:
            url = 'https://www.jstor.org' + url
            return_list.append({'url':url, 'xueKeLeiBie':xueke})

        return return_list

    # 是否有下一页
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            next_page = 'https://www.jstor.org' + selector.xpath("//form[@id='searchFormTools']/div/ul/li/a[@id='next-page']/@href").extract_first()
        except:
            next_page = None

        return next_page





