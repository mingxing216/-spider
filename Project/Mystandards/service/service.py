# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import hashlib
import time
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

    # 获取列表页url
    def getCatalogUrl(self, resp):
        catalog_list = []
        selector = Selector(text=resp)
        try:
            # 获取列表页所在的a标签的url
            url_list = selector.xpath("//div[contains(@class, 'row')]//h2/a/@href").extract()
            # 遍历每个发布单位url，添加到列表中
            for i in url_list:
                url = 'https://www.mystandards.biz' + i
                catalog_list.append(url)
        except Exception:
            return catalog_list

        return catalog_list

    # 获取详情url
    def getDetailUrl(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页每个详情所在的标签
            url_list = selector.xpath("//div[contains(@class, 'searchDuplicateRow')]/div[2]")
            # 遍历元素，获取详情url、"状态"
            for i in url_list:
                url = 'https://www.mystandards.biz' + i.xpath("./a[1]/@href").extract_first()
                text = i.xpath("./p[last()]/strong[1]/text()").extract_first()
                if text:
                    field = text
                else:
                    field = ""
                return_list.append({'url': url, 'biaoZhunZhuangTai': field})
        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            next = selector.xpath("//a[@href and contains(text(), 'Next')]/@href").extract_first()
            next_page = 'https://www.mystandards.biz' + next
        except:
            next_page = None

        return next_page

    # =====================获取字段
    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标准编号
    def getBiaoZhunBianHao(self, select):
        selector = select
        try:
            biaozhunhao = selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Designation standards')]/following-sibling::text()[1]").extract_first().strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//span[@itemprop='description']/text()").extract_first()
            title = re.sub(r"-$", "", re.sub(r"[\n\r\t]", "", tit).strip()).strip()

        except Exception:
            title = ""

        return title

    # 获取出版日期
    def getChuBanRiQi(self, select):
        selector = select
        try:
            ri = selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Publication date standards')]/following-sibling::text()[1]").extract_first().strip()
            riqi = '-'.join(list(reversed(ri.split('.'))))
            try:
                date = str(datetime.strptime(riqi, "%Y-%m-%d"))
            except Exception:
                date = riqi

        except Exception:
            date = ""

        return date

    # 获取页数
    def getYeShu(self, select):
        selector = select
        try:
            yeshu = selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'The number of pages')]/following-sibling::text()[1]").extract_first().strip()

        except Exception:
            yeshu = ""

        return yeshu

    # 获取国别
    def getGuoBie(self, select):
        selector = select
        try:
            guobie = selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Country')]/following-sibling::text()[2]").extract_first().strip()

        except Exception:
            guobie = ""

        return guobie

    # 获取国际组织机构
    def getGuoJiZuZhiJiGou(self, select):
        selector = select
        try:
            zuzhijigou = selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Country')]/following-sibling::a[1]/text()").extract_first().strip()

        except Exception:
            zuzhijigou = ""

        return zuzhijigou

    # 获取国际标准分类号
    def getGuoJiBiaoZhunFenLeiHao(self, select):
        result_list = []
        selector = select
        try:
            feileihaos = selector.xpath("//p[@class='justify_p']/a/@href").extract()
            for i in feileihaos:
                # fenleihao = i.replace('/search2.html?ics1=', '').replace('ics2=', '').replace('ics3=', '').replace('&', '.')
                fenlei = list(re.findall(r"ics1=(\d*?)&ics2=(\d*?)&ics3=(\d*)", i)[0])
                # 去除列表中空元素，拼成字符串
                fenleihao = '.'.join([i for i in fenlei if i != ''])
                result_list.append(fenleihao)

        except Exception:
            return '|'.join(result_list)

        return '|'.join(result_list)

    # 获取html类型值（描述）
    def getMiaoShu(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//h2[contains(text(), 'Annotation of standard text')]/following-sibling::p[1]")[0]
            htmlValue = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            htmlValue = ""

        return htmlValue

    # 关联文档
    def guanLianWenDang(self, select):
        selector = select
        e = {}
        try:
            e['url'] = selector.xpath("//a[text()='Preview']/@href").extract_first().strip()
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # 关联机构
    def guanLianJiGou(self, select):
        selector = select
        e = {}
        try:
            e['url'] = 'https://www.mystandards.biz' + selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Country')]/following-sibling::a[1]/@href").extract_first().strip()
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '机构'
        except Exception:
            return e

        return e

    # 获取价格
    def getPrice(self, select):
        selector = select
        price_list = []
        try:
            language = selector.xpath("//select[contains(@class, 'selectpicker')]/option/text()").extract()
            prices = selector.xpath("//span[contains(@class, 'lang')]")
            Availability = selector.xpath("//td[@class='ffSklad']/span/span//text()").extract_first().strip()
            for i in range(len(language)):
                price = prices[i].xpath("./div[@class='radio']/label")
                for j in price:
                    dict = {}
                    dict['Language'] = language[i]
                    jiage = re.sub(r"[\r\n\t]", "", ''.join(j.xpath("./text()").extract())).strip()
                    dict['格式'] = re.findall(r"(.*)\s+-", jiage)[0]
                    dict['价格'] = re.findall(r"-\s+(.*)", jiage)[0]
                    dict['Availability'] = Availability
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

class JiGouServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)
