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

    # 获取分类url
    def getClassifyUrl(self, resp, para):
        selector = Selector(text=resp)
        try:
            classify_para = re.findall(r".*\((.*)\)", selector.xpath("//a[contains(text(), '" + para + "')]/@onclick").extract_first())[0].replace("'", "").strip()
            classify_list = classify_para.split(', ')
            classify_url = 'https://www.boutique.afnor.org/ajax/results-en/group/' + classify_list[1] + '/' + classify_list[1] + '/' + classify_list[2] + '/' + classify_list[3] + '/' + classify_list[4]

        except Exception:
            classify_url = ""

        return classify_url

    # 获取列表页url
    def getCatalogUrl(self, resp, key):
        catalog_list = []
        selector = Selector(text=resp)
        try:
            # 获取列表页url
            tags = selector.xpath("//a")
            for tag in tags:
                catalog_dict = {}
                catalog_dict['url'] = 'https://www.boutique.afnor.org' + tag.xpath("./@href").extract_first()
                catalog_dict[key] = re.sub(r"\(.*\)", "", tag.xpath("./text()").extract_first()).strip()
                catalog_list.append(catalog_dict)

        except Exception:
            return catalog_list

        return catalog_list

    # 获取详情url
    def getDetailUrl(self, resp, k, v):
        return_list = []
        selector = Selector(text=resp)
        try:
            # 获取一页每个详情所在的标签
            url_list = selector.xpath("//div[@class='bloc-resultat-livre']/div[@class='conteneur-livre']/div/h3/a/@href").extract()
            # 遍历元素，获取详情url、"状态"
            for i in url_list:
                url = i.strip()
                return_list.append({'url': url, k: v})
        except Exception:
            return return_list

        return return_list

    # 获取总页数
    def getTotalPage(self, resp):
        selector = Selector(text=resp)
        try:
            last = selector.xpath("//script[contains(text(), 'lastPage')]/text()").extract_first()
            total_page = re.findall(r".*lastPage = (\d+);.*", last)[0].strip()
        except:
            total_page = None

        return total_page

    # =====================获取字段
    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标准编号
    def getBiaoZhunBianHao(self, select):
        selector = select
        try:
            biaozhunhao = selector.xpath("//div[@class='desc']/h1/text()").extract_first().strip()

        except Exception:
            biaozhunhao = ""

        return biaozhunhao

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//div[@class='bloc-ombre']/p/text()").extract_first()
            title = re.sub(r"[\n\r\t]", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取标准状态
    def getBiaoZhunZhuangTai(self, select):
        selector = select
        try:
            zhuang = selector.xpath("//span[@class='mention-annule']/text()").extract_first().strip()
            zhuangtai = re.findall(r"(.*?)\s+.*", zhuang)[0].strip()

        except Exception:
            zhuangtai = ""

        return zhuangtai

    # 获取标准发布组织
    def getBiaoZhunFaBuZuZhi(self, select):
        selector = select
        try:
            zuzhi = selector.xpath("//span[@class='publisher_name']/text()").extract_first().strip()
            fabuzuzhi = re.findall(r"(.*)[,，]\s*\d+", zuzhi)[0].strip()

        except Exception:
            fabuzuzhi = ""

        return fabuzuzhi

    # 获取html类型值（摘要）
    def getMuLu(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//div[contains(@class, 'entete-fiche')]/div[@class='bloc-ombre']")[0]
            htmlValue = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            htmlValue = ""

        return htmlValue

    # 获取ISBN
    def getIsbn(self, select):
        return_list = []
        selector = select
        try:
            tag = selector.xpath("//div[@class='bloc-ombre']/table/tbody/tr[position()>1]")
            for i in tag:
                v = ' '.join(i.xpath("./td/text()").extract())
                return_list.append(v)

            isbn = '|'.join(return_list)

        except Exception:
            isbn = ""

        return isbn

    # 获取文本类型值（版本、ISBN、页数）
    def getField(self, select, para):
        selector = select
        try:
            fieldValue = selector.xpath("//section[@class='metadata']/dl/dt[contains(text(), '" + para + "')]//following-sibling::dd[1]/text()").extract_first().strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取出版日期
    def getRiqi(self, select):
        selector = select
        try:
            fieldValue = selector.xpath("//section[@class='metadata']/dl/dt[contains(text(), 'Published')]//following-sibling::dd[1]/text()").extract_first().strip()
            riqi = str(datetime.strptime(fieldValue, "%m/%d/%Y"))

        except Exception:
            riqi = ""

        return riqi

    # 获取代替标准、被代替标准
    def getDaiTiBiaoZhun(self, select, para):
        result_list = []
        selector = select
        try:
            biaozhun = selector.xpath("//h3[contains(text(), '" + para + "')]/following-sibling::div[1]/div")
            for i in biaozhun:
                result_dict = {}
                try:
                    result_dict['标准号'] = i.xpath(".//div[@class='conteneur-livre']//h3/a/text()").extract_first().strip()
                except Exception:
                    result_dict['标准号'] = ""
                try:
                    result_dict['链接'] = i.xpath(".//div[@class='conteneur-livre']//h3/a/@href").extract_first().strip()
                except Exception:
                    result_dict['链接'] = ""
                try:
                    result_dict['标题'] = i.xpath(".//div[@class='conteneur-livre']//p/a[@class='sous-titre']/text()").extract_first().strip()
                except Exception:
                    result_dict['标题'] = ""
                try:
                    result_dict['状态'] = i.xpath(".//div[@class='conteneur-livre']//p/span[@class='mention-annule-small']/text()").extract_first().strip()
                except Exception:
                    result_dict['状态'] = ""
                result_list.append(result_dict)

        except Exception:
            return result_list

        return result_list

    # 获取引用标准、被引用标准
    def getYinYongBiaoZhun(self, select, para):
        result_list = []
        selector = select
        try:
            biaozhun = selector.xpath("//h3[contains(text(), '" + para + "')]/../following-sibling::div[1]/div")
            for i in biaozhun:
                result_dict = {}
                try:
                    result_dict['标准号'] = i.xpath(".//div[@class='conteneur-livre']//h3/a/text()").extract_first().strip()
                except Exception:
                    result_dict['标准号'] = ""
                try:
                    result_dict['链接'] = i.xpath(".//div[@class='conteneur-livre']//h3/a/@href").extract_first().strip()
                except Exception:
                    result_dict['链接'] = ""
                try:
                    result_dict['标题'] = i.xpath(".//div[@class='conteneur-livre']//p/a[@class='sous-titre']/text()").extract_first().strip()
                except Exception:
                    result_dict['标题'] = ""
                try:
                    result_dict['状态'] = i.xpath(".//div[@class='conteneur-livre']//p/span[@class='mention-annule-small']/text()").extract_first().strip()
                except Exception:
                    result_dict['状态'] = ""
                result_list.append(result_dict)

        except Exception:
            return result_list

        return result_list

    # 关联文档
    def guanLianWenDang(self, select):
        selector = select
        e = {}
        try:
            e['url'] = 'https://www.boutique.afnor.org/' + selector.xpath("//a[@class='preview']/@href").extract_first().strip()
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
            e['url'] = 'https://www.boutique.afnor.org/' + selector.xpath("//h2[contains(text(), 'The information about the standard:')]/following-sibling::p[1]/strong[contains(text(), 'Country')]/following-sibling::a[1]/@href").extract_first().strip()
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '机构'
        except Exception:
            return e

        return e

    # 获取价格所在标签
    def getTag(self, select):
        selector = select
        try:
            tag = selector.xpath("//ol[@id='available_editions']")[0]
        except Exception:
            tag = None

        return tag

    # 获取价格
    def getPrice(self, select):
        selector = select
        price_list = []
        try:
            language = selector.xpath("//select[@id='language_selector']/option[@selected]/text()").extract_first().strip()
            prices = selector.xpath("//li[contains(@class, 'product_row')]/ul")
            for i in range(len(prices)):
                price_dict = {}
                price_dict['Language'] = language
                price_dict['Available formats'] = prices[i].xpath("./li[@class='edition']/text()").extract_first().strip()
                price_dict['Availability'] = prices[i].xpath("./li[@class='availability']/text()").extract_first().strip()
                price_dict['Priced Form（in USD）'] = prices[i].xpath("./li[@class='price']/span/text()").extract_first().strip()
                price_list.append(price_dict)

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

    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1/text()").extract_first()
            title = re.sub(r"[\n\r\t]", "", tit).strip()

        except Exception:
            title = ""

        return title

    # 获取标识
    def getBiaoShi(self, select):
        selector = select
        try:
            img = selector.xpath("//h1/preceding-sibling::img[1]/@src").extract_first().strip()
            img_src = 'https://www.mystandards.biz' + img

        except Exception:
            img_src = ""

        return img_src

    # 获取简介
    def getJianJie(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//h1/following-sibling::p[1]")[0]
            htmlValue = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            htmlValue = ""

        return htmlValue

    # 图片关联机构url
    def guanLianJiGou(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '机构'
        except Exception:
            return e

        return e