# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import json
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import redis_pool

etree = html.etree


def error(func):
    def wrapper(self, *args, **kwargs):
        if args[0]:
            data = func(self, *args, **kwargs)
            return data
        else:
            return None

    return wrapper


class UrlServer(object):
    def __init__(self, logging):
        self.logging = logging
        self.redis_client = redis_pool.RedisPoolUtils()

    # 获取跟栏目数量
    @error
    def getColumnNumber(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        column_number = 0
        div_list = html_etree.xpath("//div[@class='guide']")
        for div in div_list:
            column_number += 1

        return column_number
    
    @error
    def getColumnSunData(self, resp):
        return_data = []
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//li")
        for li in li_list:
            column_name = li.xpath("./span[@class='refirstcol']/a/@title")[0]
            dd_list = li.xpath("./dl[@class='resecondlayer']/dd")
            for dd in dd_list:
                data = {}
                data['column_name2'] = dd.xpath("./a/@title")[0]
                data['column_name'] = column_name + '_' + dd.xpath("./a/@title")[0]
                onclick_data = dd.xpath("./a/@onclick")[0]
                data_tuple = re.findall(r"(\(.*\))", onclick_data)[0]  # 数据元祖
                data_tuple = "(" + ''.join(re.findall(r"[^()]", data_tuple)) + ")"
                try:
                    data_tuple = eval(data_tuple)
                    data['name'] = data_tuple[1]
                    data['value'] = data_tuple[2]
                    data['has_next'] = True
                    data['column_name1'] = column_name
                    return_data.append(data)
                except:

                    continue

        return return_data
    
    @error
    def createTaskQueue(self, resp, column_name, redis_name, redis_name2, requests_data):
        '''
        生成期刊主页任务队列， 获取总期刊数
        :param html: 期刊列表页源码
        :return: 总期刊数
        '''
        column_name1 = requests_data['column_name1']
        column_name2 = requests_data['column_name2']

        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//ul[@class='list_tup']/li")
        try:
            # 总期刊数
            qikan_number = re.findall(r"(\d+)", html_etree.xpath("//div[@class='pagenav']/text()")[0])[0]
        except:
            return None

        i = 0
        for li in li_list:
            queue_data = {}
            if i == 0:
                i += 1
                continue
            title = li.xpath("./a/@title")[0]
            href = li.xpath("./a/@href")[0]
            pcode = re.findall(r"pcode=(.*?)&", href)[0]
            pykm = re.findall(r"&baseid=(.*)", href)[0]
            url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)
            queue_data["column_name"] = column_name
            queue_data["title"] = title
            queue_data["url"] = url
            queue_data["column_name1"] = column_name1
            queue_data["column_name2"] = column_name2
            queue_data["qikan_number"] = qikan_number
            print(queue_data)
            # 生成期刊文章对应的期刊url队列
            self.redis_client.sadd(redis_name, json.dumps(queue_data))
            # 生成期刊抓取任务队列
            self.redis_client.sadd(redis_name2, json.dumps(queue_data))

            self.logging.info('栏目名: {} | 子栏目名: {} | 期刊数量: {} | 组合栏目名: {} | 期刊名: {} | 期刊url: {}'
                         .format(column_name1, column_name2, qikan_number, column_name, title, url))

        return qikan_number


class QiKanServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 获取期刊标题
    @error
    def getTitle(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            title = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', html_etree.xpath("//h3[@class='titbox']/text()")[0]))
        except:
            title = ''

        return title

    # 获取核心收录
    @error
    def getHeXinShouLu(self, resp):
        return_data = []
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        if html_etree.xpath("//p[@class='journalType']/span"):
            span_list = html_etree.xpath("//p[@class='journalType']/span")
            for span in span_list:
                try:
                    title = span.xpath("./@title")[0]
                    return_data.append(title)
                except:
                    pass

        return '|'.join(return_data)

    # 获取英文名称
    @error
    def getYingWenMingCheng(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            p_text = html_etree.xpath("//dd[@class='infobox']/p[not(@class)]/text()")[0]
            data = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', p_text))

            return data
        except:
            p_text = ''

            return p_text

    # 获取图片
    @error
    def getBiaoShi(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            pic_url = html_etree.xpath("//dt[@id='J_journalPic']/img/@src")[0]
        except:
            pic_url = ''

        return 'http:' + pic_url

    # 多字段获取公共方法
    @error
    def getData(self, resp, text):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//ul[@id='JournalBaseInfo']/li[not(@class)]/p")
        for li in li_list:
            try:
                if li.xpath("./text()")[0] == str(text):
                    name = li.xpath("./span/text()")[0]
                    return name
            except:

                return ''

        return ''

    # 多字段获取公共方法2
    @error
    def getData2(self, resp, text):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//ul[@id='publishInfo']/li[not(@class)]/p")
        for li in li_list:
            try:
                if li.xpath("./text()")[0] == str(text):
                    name = li.xpath("./span/text()")[0]
                    return name
            except:

                return ''

        return ''

    # 获取复合影响因子
    @error
    def getFuHeYingXiangYinZi(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p")
        for li in li_list:
            try:
                if '复合影响因子' in li.xpath("./text()")[0]:
                    key = re.findall(r"\d+版", li.xpath("./text()")[0])[0]
                    value = li.xpath("./span/text()")[0]

                    return {
                        '因子年版': key,
                        '因子数值': value
                    }
            except:

                return {}

        return {}

    # 获取综合影响因子
    @error
    def getZongHeYingXiangYinZi(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        li_list = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p")
        for li in li_list:
            try:
                if '综合影响因子' in li.xpath("./text()")[0]:
                    key = re.findall(r"\d+版", li.xpath("./text()")[0])[0]
                    value = li.xpath("./span/text()")[0]

                    return {
                        '因子年版': key,
                        '因子数值': value
                    }
            except:

                return {}

        return {}

    # 获取来源数据库
    @error
    def getLaiYuanShuJuKu(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            database = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[@class='database']/@title")[0]
        except:
            database = ''

        return database

    # 获取期刊荣誉
    @error
    def getQiKanRongYu(self, resp):
        response = bytes(bytearray(resp.content.decode('utf-8'), encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            data = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[text()='期刊荣誉：']/following-sibling::p[1]/span/text()")[0]
        except:
            data = ''

        return data.replace(';', '|')


class Server(object):
    def __init__(self, logging):
        self.logging = logging

    @error
    def getTitle(self, resp):
        '''This is demo'''
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        title = response_etree.xpath("//title/text()")[0]

        return title






