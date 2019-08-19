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
            biaozhunhao = selector.xpath("//h1/text()").extract_first().strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1/following-sibling::p[1]/text()").extract_first()
            title = re.sub(r"\n", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取html类型值（摘要、描述）
    def getHtmlField(self, html, value):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//a[contains(text(), '" + value + "')]/../following-sibling::div[1]//div[@class='wysiwyg-content']/p")[0]
            htmlValue = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            htmlValue = ""

        return htmlValue

    # 获取文本类型值（标准类型、标准状态、标准发布组织）
    def getField(self, select, para):
        selector = select
        try:
            result = selector.xpath("//strong[contains(text(), '" + para + "')]/../following-sibling::td[1]/text()").extract_first().strip()

        except Exception:
            result = ""

        return result

    # 获取标准发布组织
    def getFaBuZuZhi(self, select):
        selector = select
        try:
            result = selector.xpath("//span[@id='lnkPublisherGeneral']/text()").extract_first().strip()

        except Exception:
            result = ""

        return result

    # 获取序列字段（被代替标准、代替标准）
    def getXuLieField(self, select, para):
        result = []
        selector = select
        try:
            biaozhun = selector.xpath("//strong[contains(text(), '" + para + "')]/../following-sibling::td[1]/ul/li/a")
            for i in range(len(biaozhun)):
                dict = {}
                try:
                    dict['标准号'] = biaozhun[i].xpath("./text()").extract_first().strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = 'https://infostore.saiglobal.com' + biaozhun[i].xpath("./@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""

                result.append(dict)

        except Exception:
            return result

        return result

    # 获取引用标准
    def getYinYongBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhun = selector.xpath("//a[contains(text(), 'Standards Referenced By This Book')]/../following-sibling::div[1]//table//a")
            for i in range(len(biaozhun)):
                dict = {}
                try:
                    dict['标准号'] = biaozhun[i].xpath("./text()").extract_first().strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = 'https://infostore.saiglobal.com' + biaozhun[i].xpath("./@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    dict['标题'] = biaozhun[i].xpath("../../following-sibling::td[1]/text()").extract_first().strip()
                except Exception:
                    dict['标题'] = ""

                result.append(dict)

        except Exception:
            return result

        return result

    # 获取国际标准类别
    def getGuoJiBiaoZhunLeiBie(self, html):
        tree = etree.HTML(html)
        result_list = []
        try:
            result = tree.xpath("//h2[text()='Category']/../small")
            for i in result:
                lei = re.sub(r"[\n\r\t]", "", tostring(i).decode('utf-8')).strip()
                result_list.append(lei)
            leibie = '\n'.join(result_list)

        except Exception:
            leibie = ""

        return leibie

    # 获取等效标准
    def getDengXiaoBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhun = selector.xpath("//a[contains(text(), 'International Equivalents – Equivalent Standard(s) & Relationship')]/../following-sibling::div[1]//table//a")
            for i in range(len(biaozhun)):
                dict = {}
                try:
                    dict['Equivalent Standard(s)'] = biaozhun[i].xpath("./text()").extract_first().strip()
                except Exception:
                    dict['Equivalent Standard(s)'] = ""
                try:
                    dict['链接'] = 'https://infostore.saiglobal.com' + biaozhun[i].xpath("./@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    dict['Relationship'] = biaozhun[i].xpath("../following-sibling::td[1]/text()").extract_first().strip()
                except Exception:
                    dict['Relationship'] = ""

                result.append(dict)

        except Exception:
            return result

        return result

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

    # 获取variationSKU
    def getSku(self, select):
        selector = select
        try:
            faburiqi = selector.xpath("//select[contains(@class, 'ddlProductVariations')]/option[@selected]/@value").extract_first().strip()

        except Exception:
            faburiqi = ""

        return faburiqi

    # 获取发布日期
    def getFaBuRiQi(self, json):
        json_dict = json
        try:
            faburiqi = json_dict['d']['PublicationDate']

        except Exception:
            faburiqi = ""

        return faburiqi

    # 获取页数
    def getYeShu(self, json):
        json_dict = json
        try:
            yeshu = json_dict['d']['Pages']

        except Exception:
            yeshu = ""

        return yeshu

    # 获取国际标准书号
    def getIsbn(self, json):
        json_dict = json
        try:
            isbn = json_dict['d']['ISBN']

        except Exception:
            isbn = ""

        return isbn

    # 获取价格接口参数及价格名称
    def getName(self, select):
        selector = select
        price_list = []
        try:
            skus = selector.xpath("//select[contains(@class, 'ddlProductVariations')]/option/@value").extract()
            names = selector.xpath("//select[contains(@class, 'ddlProductVariations')]/option/text()").extract()
            for i in range(len(skus)):
                sku = skus[i]
                name = names[i]
                price_list.append((sku, name))

        except Exception:
            return price_list

        return price_list

    # 获取价格
    def getPrice(self, json):
        json_dict = json
        try:
            price = '$' + str(json_dict['d']['Price'])

        except Exception:
            price = ""

        return price

    # 获取版本
    def getBanBen(self, select):
        selector = select
        try:
            ban = selector.xpath("//ul[@class='product-details-list']/li/strong[contains(text(), 'Revision')]/following-sibling::span[1]/text()").extract_first()
            banben = re.findall(r"(.*Edition)", ban)[0].strip()

        except Exception:
            banben = ""

        return banben



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
    def guanLianBiaoZhun(self, url):
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