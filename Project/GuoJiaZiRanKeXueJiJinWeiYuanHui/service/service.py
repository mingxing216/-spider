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

    # 获取研究领域名称及种子
    def getCatalogList(self, json):
        return_data = []
        try:
            datas = json['data']
            for data in datas:
                dict = {}
                dict['code'] = data['code']
                # 请求第一页
                dict['num'] = 0
                dict['xueKeLeiBie'] = data['depC']
                dict['totalCount'] = data['num']
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # 获取详情种子
    def getDetailUrl(self, json, xuekeleibie):
        return_data = []
        try:
            datas = json['data']
            for data in datas:
                data['xueKeLeiBie'] = xuekeleibie
                data['chineseTitle'] = re.sub(r"(\(|（)[^\(（）\)]*?(）|\))$", "", data['chineseTitle']).strip()
                t = round(time.time()* 1000)
                data['url'] = 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_default_result_aspx&isinEn=1&dbPrefix=SCDB&dbCatalog=%e4%b8%ad%e5%9b%bd%e5%ad%a6%e6%9c%af%e6%96%87%e7%8c%ae%e7%bd%91%e7%bb%9c%e5%87%ba%e7%89%88%e6%80%bb%e5%ba%93&ConfigFile=SCDBINDEX.xml&research=off&t=' + str(t) + '&keyValue=' + quote(data['chineseTitle']) + '&S=1&sorttype='
                return_data.append(data)

        except Exception:
            return return_data

        return return_data

    # ---------------------
    # data script
    # ---------------------

    # ====== 论文实体
    def getFieldValue(self, json, para):
        try:
            value = json['data'][0][para]
            if isinstance(value, str):
                value = value.strip()

        except Exception:
            value = ""

        return value

    def getMoreFieldValue(self, json, para):
        try:
            value = json['data'][0][para]
            if ';' in value or '；' in value:
                values = re.sub(r"\s*[;；]\s*", "|", value).strip()
            else:
                values = re.sub(r"\s*[,，]\s*", "|", value).strip()

        except Exception:
            values = ""

        return values

    def hasChinese(self, json, para):
        journal = json['data'][0][para]
        for ch in journal:
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

    # 关联文档
    def guanLianWenDang(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # ====== 文档实体
    # 关联论文
    def guanLianLunWen(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e


























