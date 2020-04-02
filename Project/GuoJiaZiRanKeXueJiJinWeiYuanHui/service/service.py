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
                dict = {}
                dict['id'] = data['id']
                dict['xueKeLeiBie'] = xuekeleibie
                dict['url'] = 'http://ir.nsfc.gov.cn/paperDetail/' + data['id']
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # ---------------------
    # data script
    # ---------------------

    # ====== 论文实体
    def getFieldValue(self, json, para):
        try:
            value = json['data'][0][para].strip()

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

    def getXueKeLeiBie(self, json, para, xueke):
        try:
            value = json['data'][0][para].strip()
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


























