# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import time
from urllib.parse import quote,unquote
import requests
import hashlib
from lxml import etree
from lxml.html import fromstring, tostring
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

    # 获取期刊名录总页数
    def getJournalPages(self, text):
        return_data = []
        selector = Selector(text=text)
        try:
            a_list = selector.xpath("//h2[contains(text(),'学科分类')]/following-sibling::ul[1]/li/a")
            for a in a_list:
                a_dict = {}
                href = a.xpath("./@href").extract_first()
                para = ast.literal_eval(re.findall(r"showlist(\(.*\))", href)[0])
                # 请求第一页
                # a_dict['num'] = 0
                a_dict['url'] = 'http://www.nssd.org/journal/list.aspx?p=1&t=0&e={}&h={}'.format(quote(para[0]),
                                                                                                 quote(para[1]))
                a_dict['xuekefenlei'] = a.xpath("./text()").extract_first()
                return_data.append(a_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊详情种子及附加信息
    def getJournalList(self, text):
        return_data = []
        selector = Selector(text=text)
        try:
            href_list = selector.xpath("//td[@class='title']/a/@href").extract()
            for href in href_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + href
                data_dict['s_xuekeleibie'] = ""
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # 获取学科分类名称及种子
    def getCatalogList(self, text):
        return_data = []
        selector = Selector(text=text)
        try:
            a_list = selector.xpath("//h2[contains(text(),'学科分类')]/following-sibling::ul[1]/li/a")
            for a in a_list:
                a_dict = {}
                href = a.xpath("./@href").extract_first()
                para = ast.literal_eval(re.findall(r"showlist(\(.*\))", href)[0])
                # 请求第一页
                # a_dict['num'] = 0
                a_dict['url'] = 'http://www.nssd.org/journal/list.aspx?p=1&t=0&e={}&h={}'.format(quote(para[0]), quote(para[1]))
                a_dict['s_xuekefenlei'] = a.xpath("./text()").extract_first()
                return_data.append(a_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊列表页总页数
    def getTotalPage(self, text):
        selector = Selector(text=text)
        try:
            span = selector.xpath("//span[@class='total']/text()").extract_first()
            total_page = re.findall(r"\d+/(\d+)", span)[0]

        except Exception:
            return 1

        return total_page

    # 获取期刊详情种子及附加信息
    def getQiKanDetailUrl(self, text, xuekeleibie):
        return_data = []
        selector = Selector(text=text)
        try:
            href_list = selector.xpath("//ul[@class='cover_list']/li/a[@class='name']/@href").extract()
            for href in href_list:
                data_dict = {}
                data_dict['s_xuekeleibie'] = xuekeleibie
                data_dict['url'] = 'http://www.nssd.org' + href
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊年列表
    def getYears(self, text, xuekeleibie):
        selector = Selector(text=text)
        try:
            a_list = selector.xpath("//div[@id='qkyearslist']/ul/li/a")
            for a in a_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + a.xpath("./@href").extract_first().strip()
                data_dict['year'] = a.xpath("./text()").extract_first().strip().replace('年', '')
                data_dict['xuekeleibie'] = xuekeleibie

                yield data_dict

        except Exception:
            return

    # 获取期号列表
    def getIssues(self, text):
        selector = Selector(text=text)
        try:
            a_list = selector.xpath("//div[@id='numlist']/ul/li/a")
            for a in a_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + a.xpath("./@href").extract_first().strip()
                data_dict['issue'] = re.findall(r"年(.*)期", a.xpath("./text()").extract_first().strip())[0]

                yield data_dict

        except Exception:
            return

    # 获取期论文刊详情种子及附加信息
    def getLunWenDetailUrl(self, text, qikanUrl, xuekeleibie, year, issue):
        return_data = []
        selector = Selector(text=text)
        try:
            tr_list = selector.xpath("//table[@class='t_list']//tr[position()>1]")
            for tr in tr_list:
                data_dict = {}
                try:
                    data_dict['url'] = 'http://www.nssd.org' + tr.xpath("./td[1]/a/@href").extract_first().strip()
                except:
                    continue
                try:
                    data_dict['authors'] = re.sub(r"[;；]", "|", tr.xpath("./td[2]/text()").extract_first().strip())
                except:
                    data_dict['authors'] = ''
                try:
                    data_dict['pdfUrl'] = 'http://www.nssd.org' + tr.xpath("./td[3]/a/@href").extract_first().strip()
                except:
                    data_dict['pdfUrl'] = ''
                data_dict['id'] = re.findall(r"id=(.*)?&?", data_dict['url'])[0]
                data_dict['qikanUrl'] = qikanUrl
                data_dict['xuekeleibie'] = xuekeleibie
                data_dict['year'] = year
                data_dict['issue'] = issue
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # ---------------------
    # data script
    # ---------------------

    # ====== 论文实体
    # 标题
    def getTitle(self, text):
        selector = Selector(text=text)
        try:
            title = selector.xpath("//h1/span/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    def getFieldValue(self, value):
        try:
            if isinstance(value, str):
                value = value.strip()

        except Exception:
            value = ""

        return value

    def getMoreFieldValue(self, value):
        '''
        多值可能有四种情况：
        1、多个作者之间以 ";" 或者 "；" 分隔；姓名之间以 " "或"," 分隔；如：http://ir.nsfc.gov.cn/paperDetail/17f8c78b-1c38-4103-ae69-40d2ccd16a2b
        2、多个作者之间以 "，" 分隔；姓名之间以 " "或"," 分隔；如：http://ir.nsfc.gov.cn/paperDetail/2413b709-6eef-453a-a82d-936f69b67173
        3、多个作者之间以 "," 分隔；姓名之间以 " " 分隔；
        4、多个作者之间以 "," 分隔；姓名之间以 "," 分隔；暂未发现该情况，也未解决；

        '''
        try:
            if ';' in value or '；' in value:
                values = re.sub(r"\s*[;；]\s*", "|", value).strip()
            else:
                if '，' in value:
                    values = re.sub(r"\s*[，]\s*", "|", value).strip()
                else:
                    values = re.sub(r"\s*[,]\s*", "|", value).strip()

        except Exception:
            values = ""

        return values

    def hasChinese(self, data):
        for ch in data:
            if '\u4e00' <= ch <= '\u9fa5':
                return True

        return False


    def getXueKeLeiBie(self, json, para, xueke):
        try:
            value = str(json['data'][0][para]).strip()
            if value:
                xuekeleibie = xueke + '_' + value
            else:
                xuekeleibie = xueke

        except Exception:
            xuekeleibie = xueke

        return xuekeleibie

    # 获取文档
    def getDocs(self, pdfData, size):
        labelObj = {}
        return_docs = []
        try:
            if pdfData:
                if pdfData['url']:
                    picObj = {
                        'url': pdfData['url'],
                        'title': pdfData['bizTitle'],
                        'desc': "",
                        'sha': hashlib.sha1(pdfData['url'].encode('utf-8')).hexdigest(),
                        'format': 'PDF',
                        'size': size,
                        'ss': 'document'
                    }
                    return_docs.append(picObj)
                labelObj['全部'] = return_docs
        except Exception:
            labelObj['全部'] = []

        return labelObj

    # 关联文档
    def guanLianWenDang(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # ====== 文档实体
    # 关联论文
    def guanLianLunWen(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e


























