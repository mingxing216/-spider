# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


class Service_58TongCheng(object):
    def __init__(self):
        pass

    # 提取地区分类url
    def getAddUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//dl[@id='clist']//a/@href"):
            url_list = resp_etree.xpath("//dl[@id='clist']//a/@href")
            for url in url_list:
                return_data.append('https:' + str(re.sub(r"\s+", "", url)))
            logging.info('提取地区分类url成功')
        else:
            logging.error('提取地区分类url失败')
            return return_data

        return return_data

    # 提取行业分类url
    def getIndustryUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//dl[@class='selIndCate']//a"):
            a_list = resp_etree.xpath("//dl[@class='selIndCate']//a")
            for a in a_list:
                if a.xpath("./text()")[0] == '全部':
                    continue
                if a.xpath("./@href")[0] == 'javascript:showGrade()':
                    continue
                url = 'https:' + a.xpath("./@href")[0]
                return_data.append(url)
            logging.info('提取行业分类url成功')
        else:
            logging.error('提取行业分类url失败')
            return return_data

        return return_data

    # 判断当前页是否有公司数据
    def getPageStatus(self, logging, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='compList']//a"):
            return True
        else:
            logging.error('已到达末页')
            return False

    # 获取当前页公司名称列表
    def getCompantList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        company_list = resp_etree.xpath("//div[@class='compList']//a/text()")
        for company in company_list:
            name = re.sub(r"\.+", "", company)
            return_data.append(name)

        return return_data


