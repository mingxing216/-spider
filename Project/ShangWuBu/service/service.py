# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import requests
from lxml import etree
from lxml.html import fromstring, tostring
from urllib.parse import quote,unquote
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class Server(object):
    def __init__(self, logging):
        self.logging = logging

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取id
    def getId(self, url):
        id = re.findall(r"sortId=(\d+)&?", url)[0]
        return id

    # 获取
    def getYearList(self, resp, id, year_url, es, clazz, para):
        return_data = []
        selector = Selector(text=resp)
        try:
            dd_list = selector.xpath("//dl[dt[contains(text(), '{}')]]/dd".format(para))
            for dd in dd_list:
                dict = {}
                dd_href_list = ast.literal_eval(re.findall(r"(\(.*\))", dd.xpath("./a/@href").extract_first().strip())[0])
                dd_time = re.findall(r"(.*?)\s*[\(\（]", dd.xpath("./a/text()").extract_first().strip())[0]
                dict['url'] = year_url.format(id, quote(dd_href_list[0]), quote(dd_href_list[1]), quote(dd_href_list[2]))
                dict['nianfen'] = {'Y': dd_time}
                dict['es'] = es
                dict['clazz'] = clazz
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # 获取详情种子
    def getDetailUrl(self, resp, nianfen, es, clazz):
        return_data = []
        selector = Selector(text=resp)
        try:
            href_list = selector.xpath("//p[@class='p1']/a/@href").extract()
            for href in href_list:
                if 'http' not in href:
                    href = 'http://policy.mofcom.gov.cn' + href.strip()

                dict = {}
                dict['url'] = href.strip()
                dict['nianfen'] = nianfen
                dict['es'] = es
                dict['clazz'] = clazz
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # 获取下一页url
    def totalPages(self, resp):
        selector = Selector(text=resp)
        try:
            pages = selector.xpath("//div[contains(@class, 'blank')]/span[contains(@class, 's2')]/text()").extract_first().strip()
            total_page = re.findall(r"\/(\d+)页", pages)[0]

        except Exception:
            total_page = 1

        return total_page


    # ---------------------
    # data script
    # ---------------------

    # ====== 法律实体
    def getTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title = selector.xpath("//h2/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    def getContent(self, html):
        tree = etree.HTML(html)
        try:
            tag = tree.xpath("//div[@class='article']")[0]
            html_value = re.sub(r"[\n\r\t]", "", tostring(tag, encoding='utf-8').decode('utf-8')).strip()

        except Exception:
            html_value = ""

        return html_value

    def getInfoUrl(self, resp):
        selector = Selector(text=resp)
        try:
            href = selector.xpath("//ul[@class='toolbarList']/li/a[contains(text(), '基')]/@href").extract_first().strip()
            if 'http' not in href:
                href = 'http://policy.mofcom.gov.cn' + href

        except Exception:
            href = ""

        return href

    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            field_value = selector.xpath("//td[span[contains(text(), '{}')]]/text()".format(para)).extract_first().strip()
        except Exception:
            field_value = ""

        return field_value

    def getMoreField(self, resp, para):
        selector = Selector(text=resp)
        try:
            field_name = selector.xpath("//td[span[contains(text(), '{}')]]/text()".format(para)).extract_first().strip()
            field_value = re.sub(r"[\n\r\t]", "", field_name).replace(';', '|').replace('；', '|')

        except Exception:
            field_value = ""

        return field_value





























