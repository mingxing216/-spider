# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import hashlib
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

    # 获取所有发布单位列表url
    def getPublishUrlList(self, resp, index_url):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取所有发布单位所在的a标签的url
            url_list = selector.xpath("//select[@class='drpPublisher']/option[not(contains(text(), 'Publisher'))]/@value").extract()
            # 遍历每个发布单位url，添加到列表中
            for i in url_list:
                url = index_url + '&publisher=' + i
                return_list.append(url)
        except Exception:
            return return_list

        return return_list

    # 获取列表页url
    def getCatalogUrl(self, resp, pub_url):
        catalog_list = []
        selector = Selector(text=resp)
        try:
            # 获取列表页所在的a标签的url
            url_list = selector.xpath("//select[@class='drpCategory']/option[not(contains(text(), 'Category'))]/@value").extract()
            # 遍历每个发布单位url，添加到列表中
            for i in url_list:
                url = pub_url + '&categoryID=' + i
                catalog_list.append(url)
        except Exception:
            return catalog_list

        return catalog_list

    # 获取详情url
    def getDetailUrl(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页所有详情url
            url_list = selector.xpath("//div[contains(@class, 'product-item--body')]/h2/a/@href").extract()
            # 遍历每个详情url，存入列表
            for i in url_list:
                url = 'https://infostore.saiglobal.com' + i
                return_list.append({'url':url})
        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            next = selector.xpath("//a[@class='search-pagination' and contains(text(), '>')]/@href").extract_first()
            next_page = 'https://infostore.saiglobal.com' + next
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
            biaozhunhao = selector.xpath("//h1[contains(@class, 'basic-info-header-docno')]/text()").extract_first().strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1[@class='doc-title']/text()").extract_first()
            title = re.sub(r"\n", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取版本
    def getBanBen(self, select):
        selector = select
        try:
            ban = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Revision')]/following-sibling::span[1]/text()").extract_first()
            banben = re.findall(r"(.*Edition)", ban)[0].strip()

        except Exception:
            banben = ""

        return banben

    # 获取出版日期
    def getChuBanRiQi(self, select):
        selector = select
        try:
            chuban = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Published Date')]/../text()").extract()
            chubanriqi = re.sub(r"[\n\r\t]", "", ''.join(chuban)).strip()

        except Exception:
            chubanriqi = ""

        return chubanriqi

    # 获取字段值
    def getField(self, select, para):
        selector = select
        try:
            field = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), '" +  para + "')]/../text()").extract()
            fieldValue = re.sub(r"[\n\r\t]", "", ''.join(field)).strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取标准发布组织
    def getFaBuZuZhi(self, select):
        selector = select
        try:
            zuzhi = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Published By')]/following-sibling::a[1]/text()").extract_first().strip()

        except Exception:
            zuzhi = ""

        return zuzhi

    # 获取摘要
    def getZhaiYao(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//div[@class='abstract-section']")[0]
            zhaiyao = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取被代替标准
    def getBeiDaiTiBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhunhao = selector.xpath("//div[@class='doc-detail-button']/following-sibling::div[@class='hidden']/a[@class='doc-detail-link']/text()").extract()
            link = selector.xpath("//div[@class='doc-detail-button']/following-sibling::div[@class='hidden']/a[@class='doc-detail-link']/@href").extract()
            banben = selector.xpath("//div[@class='doc-detail-button']/following-sibling::div[@class='hidden']/div[@class='document-history-popup-revision']/span/text()").extract()
            for i in range(len(biaozhunhao)):
                dict = {}
                try:
                    dict['标准号'] = biaozhunhao[i].strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = link[i].strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    dict['版本'] = re.findall(r"(.*Edition)", banben[i])[0].strip()
                except Exception:
                    dict['版本'] = ""
                try:
                    dict['出版日期'] = re.findall(r"Edition,\s+(.*)", banben[i])[0].strip()
                except Exception:
                    dict['出版日期'] = ""
                result.append(dict)

        except Exception:
            return result

        return result

    # 获取代替标准
    def getDaiTiBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhun = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Superseded By')]/../a")
            for i in range(len(biaozhun)):
                dict = {}
                try:
                    dict['标准号'] = biaozhun[i].xpath("./text()").extract_first().strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = biaozhun[i].xpath("./@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""

                result.append(dict)

        except Exception:
            return result

        return result

   # 关联机构
    def guanLianJiGou(self, select):
        selector = select
        e = {}
        try:
            e['url'] = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Published By')]/following-sibling::a[1]/@href").extract_first().strip()
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '机构'
        except Exception:
            return e

        return e

   # 获取价格
    def getJiaGe(self, select):
        result = []
        selector = select
        try:
            geshi = selector.xpath("//div[contains(@class, 'pricing-format-cell')]/strong/text()").extract()
            xiangxi = selector.xpath("//div[contains(@class, 'pricing-details-cell')]/div[contains(@class, 'label')]/text()").extract()
            price = selector.xpath("//div[contains(@class, 'pricing-price-cell')]/span[@class='price-value-text']/text()").extract()
            for i in range(len(geshi)):
                dict = {}
                try:
                    dict['Format'] = geshi[i].strip()
                except Exception:
                    dict['Format'] = ""
                try:
                    dict['Details'] = xiangxi[i].strip()
                except Exception:
                    dict['Details'] = ""
                try:
                    dict['Price (USD)'] = price[i].strip()
                except Exception:
                    dict['Price (USD)'] = ""

                result.append(dict)

        except Exception:
            return result

        return result

   # 关联标准
    def guanLianBiaoZhun(self, select, url):
        selector = select
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
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

    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1[@class='standards_heading']/text()").extract_first()
            title = re.sub(r"\n", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取标识
    def getBiaoShi(self, select):
        selector = select
        try:
            pic = selector.xpath("//td/img/@src").extract_first().strip()

        except Exception:
            pic = ""

        return pic

    # 关联机构
    def guanLianJiGou(self, url):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '机构'
        except Exception:
            return e

        return e