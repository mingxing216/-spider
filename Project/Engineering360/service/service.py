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

    # 获取列表页url
    def getPublishUrlList(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取所有发布单位所在的a标签的url
            url_list = selector.xpath("//div[@id='standards-browse-page']/table//a/@href").extract()
            # 遍历每个发布单位url，添加到列表中
            for i in url_list:
                url = unquote(i)
                return_list.append('https://standards.globalspec.com' + url)
        except Exception:
            return return_list

        return return_list

    # 获取详情url
    def getDetailUrl(self, resp):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页所有详情url
            url_list = selector.xpath("//div[@id='search-results']/div/a/@href").extract()
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
            last_page = selector.xpath("//div[@class='pagination']/a[last()]/text()").extract_first().strip()
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
            biaozhun = selector.xpath("//h1[@class='page-title']/text()").extract_first()
            biaozhunhao = re.sub(r"[\r\n\t]", "", biaozhun).strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//span[@class='doc-name']/text()").extract_first()
            title = re.sub(r"[\r\n\t]", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取标准发布组织
    def getFaBuZuZhi(self, select):
        selector = select
        try:
            zuzhi = selector.xpath("//h1[contains(@class, 'supplier-name')]/text()").extract_first().strip()

        except Exception:
            zuzhi = ""

        return zuzhi

    # 获取字段值(出版日期,标准状态,页数)
    def getField(self, select, para):
        selector = select
        try:
            field = selector.xpath("//td[@class='label' and contains(text(), '" + para + "')]/following-sibling::td[contains(@class, 'data')]/text()").extract_first()
            fieldValue = re.sub(r"[\n\r\t]", "", field).strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取描述
    def getMiaoShu(self, html):
        tree = etree.HTML(html)
        result_list = []
        try:
            results = tree.xpath("//h5[contains(text(), 'scope')]/following-sibling::*")
            for result in results:
                zhai = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()
                result_list.append(zhai)
            zhaiyao = ''.join(result_list)

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取被代替标准
    def getBeiDaiTiBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhunhao = selector.xpath("//div[@class='document selected']/following-sibling::div[@class='document']/div[@class='document-history-card']")
            for i in range(len(biaozhunhao)):
                dict = {}
                try:
                    dict['标准号'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='document-title']/a/text()").extract_first().strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='document-title']/a/@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    dict['出版日期'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='publish-date']/text()").extract_first().strip()
                except Exception:
                    dict['出版日期'] = ""
                try:
                    dict['标题'] = biaozhunhao[i].xpath("./div[@class='document-name']/text()").extract_first().strip()
                except Exception:
                    dict['标题'] = ""
                try:
                    dict['简介'] = biaozhunhao[i].xpath("./div[@class='document-description']/text()").extract_first().strip()
                except Exception:
                    dict['简介'] = ""
                result.append(dict)

        except Exception:
            return result

        return result

    # 获取引用标准
    def getYinYongBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhun = selector.xpath("//div[@class='related-doc content-item']")
            for i in range(len(biaozhun)):
                dict = {}
                try:
                    biaozhunhao = biaozhun[i].xpath("./a[@class='title']/text()").extract_first().strip()
                    dict['标准号'] = re.findall(r"(.*?)\s+-\s+", biaozhunhao)[0].strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = biaozhun[i].xpath("./a[@class='title']/@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    tit = biaozhun[i].xpath("./a[@class='title']/text()").extract_first().strip()
                    dict['标题'] = re.findall(r"\s+-\s+(.*)", tit)[0].strip()
                except Exception:
                    dict['标题'] = ""
                try:
                    dict['状态'] = biaozhun[i].xpath("./div[@class='attributes']/span[contains(@class, 'status')]/@title").extract_first().strip()
                except Exception:
                    dict['状态'] = ""
                try:
                    ri = biaozhun[i].xpath("./div[@class='attributes']/text()").extract()
                    riqi = re.sub(r"[\r\n\t]", "", ''.join(ri)).strip()
                    if 'Published by' in riqi:
                        dict['Published by'] = re.findall(r"by\s+(.*)\s+.*", riqi)[0].strip()
                    else:
                        dict['Published by'] = ""
                except Exception:
                    dict['Published by'] = ""
                try:
                    dict['日期'] = biaozhun[i].xpath("./div[@class='attributes']/span[contains(@class, 'status')]/following-sibling::span[1]/text()").extract_first().strip()
                except Exception:
                    dict['日期'] = ""
                try:
                    dict['简介'] = biaozhun[i].xpath("./div[@class='description']/text()").extract_first().strip()
                except Exception:
                    dict['简介'] = ""
                result.append(dict)

        except Exception:
            return result

        return result

    # 获取代替标准
    def getDaiTiBiaoZhun(self, select):
        result = []
        selector = select
        try:
            biaozhunhao = selector.xpath("//div[@class='document selected']/preceding-sibling::div[@class='document']/div[@class='document-history-card']")
            for i in range(len(biaozhunhao)):
                dict = {}
                try:
                    dict['标准号'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='document-title']/a/text()").extract_first().strip()
                except Exception:
                    dict['标准号'] = ""
                try:
                    dict['链接'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='document-title']/a/@href").extract_first().strip()
                except Exception:
                    dict['链接'] = ""
                try:
                    dict['出版日期'] = biaozhunhao[i].xpath("./div[@class='document-heading']/div[@class='publish-date']/text()").extract_first().strip()
                except Exception:
                    dict['出版日期'] = ""
                try:
                    dict['标题'] = biaozhunhao[i].xpath("./div[@class='document-name']/text()").extract_first().strip()
                except Exception:
                    dict['标题'] = ""
                try:
                    dict['简介'] = biaozhunhao[i].xpath("./div[@class='document-description']/text()").extract_first().strip()
                except Exception:
                    dict['简介'] = ""
                result.append(dict)

        except Exception:
            return result

        return result

    # 获取分类号
    def getFenLeiHao(self, select):
        result = []
        selector = select
        try:
            fenlei_list = selector.xpath("//td[@class='label' and contains(text(), 'ICS')]/parent::tr")
            for fenlei in fenlei_list:
                try:
                    fen = fenlei.xpath("string(.)").extract_first().strip()
                    ics = re.sub(r"[\r\n\t]", " ", fen)
                except Exception:
                    ics = ""
                result.append(ics)
            fenleihao = '|'.join(result)

        except Exception:
            fenleihao = ""

        return fenleihao

   # 关联机构
    def guanLianJiGou(self, select):
        selector = select
        e = {}
        try:
            url = selector.xpath("//div[@class='logo-container']/a/@href").extract_first().strip()
            if url:
                e['url'] = url
                e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
                e['ss'] = '机构'
            else:
                return e
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
            title = selector.xpath("//h1[contains(@class, 'supplier-name')]/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 获取标识
    def getBiaoShi(self, select):
        selector = select
        try:
            pic = selector.xpath("//div[@class='logo-container']/a/img/@src").extract_first().strip()

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

   # 获取简介
    def getJianJie(self, html):
        result_list = []
        tree = etree.HTML(html)
        try:
            tags = tree.xpath("//div[@id='sp-profile-body']/div[not(@class='view-more')]")
            if not tags:
                tags = tree.xpath("//div[@id='sp-profile-body']/table")
            for tag in tags:
                content = re.sub(r"src=\"", "src=\"https://www.globalspec.com", tostring(tag).decode('utf-8'))
                result = re.sub(r"[\n\r\t]", "", content).strip()
                result_list.append(result)
            jianjie = ''.join(result_list)

        except Exception:
            jianjie = ""

        return jianjie

    # 获取简介中图片url
    def getJianJieUrl(self, select):
        url_list = []
        selector = select
        try:
            urls = selector.xpath("//div[@id='sp-profile-body']//img/@src").extract()
            for i in urls:
                url = 'https://www.globalspec.com' + i
                url_list.append(url)

        except Exception:
            return url_list

        return url_list

   # 获取通讯地址
    def getTongXunDiZhi(self, html):
        tree = etree.HTML(html)
        try:
            tongxun = tree.xpath("//div[@class='supplier-address']")[0]
            dizhi = re.sub(r"[\n\r\t]", "", tostring(tongxun).decode('utf-8')).strip()

        except Exception:
            dizhi = ""

        return dizhi

   # 获取字段值（电话、传真、企业类型）
    def getField(self, select, para):
        selector = select
        try:
            fieldValue = selector.xpath("//div[@class='label' and contains(text(), '" + para + "')]/following-sibling::div[@class='data']/text()").extract_first().strip()

        except Exception:
            fieldValue = ""

        return fieldValue

   # 获取主页
    def getZhuYe(self, select):
        selector = select
        try:
            zhuye = selector.xpath("//a[contains(@class, 'icon-accompanying-link')]/@href").extract_first().strip()

        except Exception:
            zhuye = ""

        return zhuye