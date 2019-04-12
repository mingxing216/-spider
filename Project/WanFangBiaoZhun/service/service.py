# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import re
import ast
import hashlib
import pypinyin
from lxml import html
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


class Task_Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getTypeUrl(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//a[@class='link ']")
        for a in a_list:
            url = a.xpath("./@href").extract_first()
            if url:
                return_data.append('http://www.wanfangdata.com.cn' + url)

        return return_data

    def getSearchWord_POST(self, resp):
        selector = Selector(text=resp)
        searchWord = selector.xpath("//textarea/text()").extract_first()

        return searchWord

    def getSearchWord_GET(self, type_url):
        searchWord = re.findall(r"searchWord=(.*)", type_url)
        if searchWord:
            return searchWord[0]
        else:
            return None

    def getPostData(self, searchWord):
        return {
            'searchType': 'standards',
            'searchWord': searchWord,
            'facetField': '$stand_Organization',
            'navSearchType': 'standards',
            'single': 'true'
        }

    def getZuZhiUrlList(self, zuzhi_data_json, searchWord_get):
        return_data = []
        data_dict = json.loads(zuzhi_data_json)
        data_list = data_dict['facetTree']
        for data in data_list[1:]:
            searchWord = searchWord_get
            facetField = data['facetField'] + ':' + data['value']
            facetName = data['showName']
            url = ('http://www.wanfangdata.com.cn/search/searchList.do?'
                   'beetlansyId=aysnsearch'
                   '&searchType=standards'
                   '&pageSize=50'
                   '&page=1'
                   '&searchWord={}'
                   '&facetField={}'
                   '&facetName={}').format(searchWord, facetField, facetName)

            return_data.append(url)

        return return_data

    def getOnclick(self, zuzhi_html):
        selector = Selector(text=zuzhi_html)
        return selector.xpath("//i[@class='icon icon_Miner']/@onclick").extract()

    def getSaveUrlList(self, onclicks):
        return_data = []
        for onclick in onclicks:
            onclick = re.sub(r"this\.id,", "", onclick)
            data = re.findall(r"(\(.*\))", onclick)
            if data:
                data_tuple = ast.literal_eval(data[0])
                _type = data_tuple[1]
                id = data_tuple[0]
                # http://www.wanfangdata.com.cn/details/detail.do?_type=standards&id=GB/T%2036749-2018
                url = 'http://www.wanfangdata.com.cn/details/detail.do?_type={}&id={}'.format(_type, id)
                return_data.append(url)

            else:
                continue

        return return_data

    def getSaveData(self, url):
        return {
            "sha": hashlib.sha1(url.encode('utf-8')).hexdigest(),
            "url": url
        }


class Data_Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getCateidPinyin(self, cateid):
        cateid_pinyin = ''
        for i in pypinyin.pinyin(cateid, style=pypinyin.NORMAL):
            cateid_pinyin += ''.join(i)

        return cateid_pinyin

    def getTitle(self, html):
        selector = Selector(text=html)

        title_data = selector.xpath("//div[@class='left_con_top']/div[@class='title']/text()").extract_first()
        if title_data:

            return re.sub(r"(\r|\n|\s{2,}|\t)", "", title_data)

        else:
            return ''

    def getYingWenBiaoTi(self, html):
        selector = Selector(text=html)

        title_data = selector.xpath("//div[@class='left_con_top']/div[@class='title']/following-sibling::div/text()").extract_first()
        if title_data:

            return title_data

        else:
            return ''

    def getBiaoZhunBianHao(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '标准编号')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data)

        else:
            return ''

    def getBiaoZhunLeiXing(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '标准类型')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data)

        else:
            return ''

    def getFaBuRiQi(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '发布日期')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data) + ' ' + '00:00:00'

        else:
            return ''

    def getBiaoZhunZhuangTai(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '状态')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data)

        else:
            return ''

    def getQiangZhiXingBiaoZhun(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '强制性标准')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data)

        else:
            return ''

    def getShiShiRiQi(self, html):
        selector = Selector(text=html)

        data = selector.xpath("//div[contains(text(), '实施日期')]/following-sibling::div/text()").extract_first()
        if data:
            return re.sub(r"(\r|\n|\t|\s)", "", data) + ' ' + '00:00:00'

        else:
            return ''

