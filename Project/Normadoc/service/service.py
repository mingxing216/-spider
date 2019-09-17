# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import hashlib
from datetime import datetime
from urllib.parse import quote,unquote
import requests
from lxml import etree
from lxml.html import fromstring, tostring
from scrapy.selector import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class BiaoZhunServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取国际组织列表
    def getPublishUrlList(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取所有国际组织所在的a标签的url
            url_list = selector.xpath("//a[@class='ms-label ' and contains(text(), 'Standards')]/following-sibling::div[1]//div[contains(@class, 'col-level')]//a/@href").extract()
            # 遍历每个组织url，添加到列表中
            for i in url_list:
                url = unquote(i)
                return_list.append('http:' + url)
        except Exception:
            return return_list

        return return_list

    # 获取列表页
    def getCatalogUrlList(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取所有国际组织所在的a标签的url
            url_list = selector.xpath("//ul[contains(@class, 'accordion')]/li//a/@href").extract()
            # 遍历每个组织url，添加到列表中
            for i in url_list:
                url = unquote(i)
                return_list.append(url)
        except Exception:
            return return_list

        return return_list

    # 获取详情url
    def getDetailUrl(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页所有详情url
            url_list = selector.xpath("//h2/a/@href").extract()
            # 遍历每个详情url，存入列表
            for url in url_list:
                return_list.append({'url':url})
        except Exception:
            return return_list

        return return_list

    # 是否有下一页(找到最后一页)
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            last_page = selector.xpath("//div[@class='toolbar-bottom']//li[@class='next']/preceding-sibling::li[1]/a/text()").extract_first().strip()
        except:
            last_page = None

        return last_page

    # =====================获取字段
    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标准编号
    def getBiaoZhunBianHao(self, select):
        selector = select
        try:
            biaozhun = selector.xpath("//h1/text()").extract_first()
            biaozhunhao = re.sub(r"[\r\n\t]", "", biaozhun).strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h2[@class='short-description']/text()").extract_first()
            title = re.sub(r"[\r\n\t]", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取标准状态
    def getZhuangTai(self, select):
        selector = select
        try:
            tag = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), 'expiration_de_validite')]")[0]
            if tag:
                zhuangtai = "失效"
            else:
                zhuangtai = "现行"

        except Exception:
            zhuangtai = "现行"

        return zhuangtai

    # 获取描述
    def getMiaoShu(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//h2[text()='Details']/following-sibling::div[1]")[0]
            zhaiyao = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取字段值(作者信息,标准发布组织,标准类型、版本、页数)
    def getField(self, select, para):
        selector = select
        try:
            field = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), '" + para + "')]/following-sibling::td[1]/text()").extract_first()
            fieldValue = re.sub(r"[\n\r\t]", "", field).strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取关键词
    def getGuanJianCi(self, select):
        selector = select
        try:
            field = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), 'Keyword')]/following-sibling::td[1]/text()").extract_first()
            fieldValue = re.sub(r"[\n\r\t]", "", field).strip().replace(';', '|')

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取国际标准分类号
    def getFenLeiHao(self, select):
        selector = select
        try:
            fenleihaos = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), 'ICS')]/following-sibling::td[1]/a/text()").extract()
            fenleihao = '|'.join(fenleihaos)

        except Exception:
            fenleihao = ""

        return fenleihao

    # 获取标准(被代替标准、引用标准)
    def getBiaoZhun(self, select, para):
        # value_list = []
        selector = select
        # tree = etree.HTML(html)
        try:
            fields = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), '" + para + "')]/following-sibling::td[1]//text()").extract()
            value_list = [i.strip() for i in fields]
            fieldValues = [value for value in value_list if (len(str(value)) != 0)]
            beiDaiTi = '|'.join(fieldValues).strip()
            # beiDaiTi = fields.xpath('string(.)').strip()
            # if fieldValue[-1] is '|':
            #     beiDaiTi = fieldValue[:-1]
            # else:
            #     beiDaiTi = fieldValue

        except Exception:
            beiDaiTi = ""

        return beiDaiTi

    # 获取日期(废止日期、确认日期)
    def getRiQi(self, select, para):
        selector = select
        try:
            riqi = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), '" + para + "')]/following-sibling::td[1]/text()").extract_first().strip()
            try:
                date = str(datetime.strptime(riqi, "%Y-%m-%d"))
            except Exception:
                date = riqi

        except Exception:
            date = ""

        return date

    # 获取修订标准(修订标准、被修订标准)
    def getXiuDing(self, select, para):
        return_list = []
        selector = select
        try:
            xiuding = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), '" + para + "')]/following-sibling::td[1]/a")
            if xiuding:
                for i in xiuding:
                    dict = {}
                    try:
                        dict['标准号'] = i.xpath("./text()").extract_first().strip()
                    except Exception:
                        dict['标准号'] = ""
                    try:
                        dict['链接'] = 'http://www.normadoc.com/english/' + i.xpath("./@href").extract_first().strip()
                    except Exception:
                        dict['链接'] = ""

                    return_list.append(dict)
            else:
                biaozhun = selector.xpath("//table[@class='data-table']/tbody/tr/th[contains(text(), '" + para + "')]/following-sibling::td[1]/text()").extract()
                value_list = [i.strip() for i in biaozhun]
                fieldValues = [value for value in value_list if (len(str(value)) != 0)]
                for j in fieldValues:
                    dict = {}
                    dict['标准号'] = j
                    dict['链接'] = ""
                    return_list.append(dict)

        except Exception:
            return return_list

        return return_list

    # 获取价格
    def getPrice(self, select):
        selector = select
        price_list = []
        try:
            value_list = selector.xpath("//table[@class='table_link']/tbody/tr")
            keys = selector.xpath("//table[@class='table_link']/thead/tr/th/text()").extract()
            for i in value_list:
                dict = {}
                values = i.xpath("./td[not(button)]")
                for j in range(len(keys)):
                    dict[keys[j]] = ''.join(values[j].xpath(".//text()").extract()).strip()
                    # jiage = re.sub(r"[\r\n\t]", "", ''.join(j.xpath("./text()").extract())).strip()
                price_list.append(dict)

        except Exception:
            return price_list

        return price_list

   # 关联标准
    def guanLianBiaoZhun(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '标准'
        except Exception:
            return e

        return e
