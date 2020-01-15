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

    # 获取行业名称及种子分类列表
    def getIndustryList(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            dl_list = selector.xpath("//div[contains(@class, 'subcatleft')]/dl")
            for dl in dl_list:
                dt_name = dl.xpath("./dt//text()").extract_first().strip()
                dd_list = dl.xpath("./dd/em")
                for dd in dd_list:
                    dict = {}
                    dd_name = dd.xpath("./a/text()").extract_first().strip()
                    dd_href = dd.xpath("./a/@href").extract_first()
                    dict['url'] = dd_href.strip()
                    dict['s_hangYe'] = dt_name + '_' + dd_name
                    return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # 获取研究领域类列表
    def getFieldList(self, resp, hangye):
        return_data = []
        selector = Selector(text=resp)
        try:
            dd_list = selector.xpath("//dt[contains(text(), '研究领域')]/following-sibling::dd[1]/em")
            for dd in dd_list:
                dict = {}
                dd_name = dd.xpath("./a/text()").extract_first().strip()
                dd_href = dd.xpath("./a/@href").extract_first()
                if 'http' not in dd_href:
                    dd_href = 'http://www.chinabgao.com' + dd_href.strip()

                dict['url'] = dd_href.strip()
                dict['s_hangYe'] = hangye
                dict['s_leiXing'] = dd_name
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data


    # 获取详情种子
    def getDetailUrl(self, resp, hangye, leixing):
        return_data = []
        selector = Selector(text=resp)
        try:
            href_list = selector.xpath("//div[@class='listcon']/dl/dt/a/@href").extract()
        except Exception:
            href_list = selector.xpath("//div[@class='col_l']/div[contains(@class, 'k_') and not(contains(@class, 'title'))]/h3/a/@href").extract()

        for href in href_list:
            if 'http' not in href:
                href = 'http://www.chinabgao.com' + href.strip()

            dict = {}
            dict['url'] = href.strip()
            dict['s_hangYe'] = hangye
            dict['s_leiXing'] = leixing
            return_data.append(dict)

        return return_data

    # 获取下一页url
    def hasNextUrl(self, resp):
        selector = Selector(text=resp)
        try:
            next_page = selector.xpath("//span[@class='pagebox_next']/a[contains(text(), '下一页')]/@href").extract_first().strip()
            if 'http' not in next_page:
                next_page = 'http://www.chinabgao.com' + next_page

        except Exception:
            next_page = ''

        return next_page


    # ---------------------
    # data script
    # ---------------------

    # ====== 报告实体
    def getTitle(self, resp):
        selector = Selector(text=resp)
        try:
            img = selector.xpath("//div[@class='arctitle']/h1/text()").extract_first().strip()

        except Exception:
            img = ""

        return img

    def getLaiYuanWangZhan(self, resp):
        selector = Selector(text=resp)
        try:
            wangzhan = selector.xpath("//span[@class='where'][1]/a[contains(text(), '报告')]/@href").extract_first().strip()
        except Exception:
            wangzhan = ""

        return wangzhan

    def getZuTu(self, resp):
        selector = Selector(text=resp)
        try:
            wangzhan = selector.xpath("//div[@class='repfm']/a/img/@src").extract_first().strip()
        except Exception:
            wangzhan = ""

        return wangzhan

    # 关联报告
    def guanLianBaoGao(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '报告'
        except Exception:
            return e

        return e

    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            field_value = selector.xpath("//li[span[contains(text(), '{}')]]/text()".format(para)).extract_first().strip()
        except Exception:
            field_value = ""

        return field_value

    def getGuanJianZi(self, resp):
        selector = Selector(text=resp)
        try:
            field_value = selector.xpath("//li[span[contains(text(), '关 键 字')]]//text()").extract()[1].strip()
        except Exception:
            field_value = ""

        return field_value

    def getDaoDu(self, html):
        tree = etree.HTML(html)
        try:
            tag = tree.xpath("//div[contains(@class, 'daodu')]/div")[0]
            html_value = re.sub(r"[\n\r\t]", "", tostring(tag, encoding='utf-8').decode('utf-8')).strip()

        except Exception:
            html_value = ""

        return html_value

    def getMuLu(self, html):
        tree = etree.HTML(html)
        try:
            tag = tree.xpath("//div[contains(@class, 'repcon-rep')]/div[contains(@class, 'bgcon')]")[0]
            html_value = re.sub(r"[\n\r\t]", "", tostring(tag, encoding='utf-8').decode('utf-8')).strip()

        except Exception:
            html_value = ""

        return html_value

    def getJiaGe(self, resp):
        selector = Selector(text=resp)
        try:
            href = selector.xpath("//li[span[contains(text(), '价格')]]/text()").extract_first()
        except Exception:
            href = ""

        return href

    # ====== 价格实体
    # 商品价格
    def getShangPinJiaGe(self, resp):
        selector = Selector(text=resp)
        price_dict = {}
        try:
            nodes = selector.xpath("//li[span[contains(text(), '价格')]]/span[@class='rjiage']/text()").extract_first().strip()
            prices = re.sub(r"\s", ",", re.sub(r"[:：]\s", "：", nodes))
            price_list = prices.split(',')
            for price in price_list:
                name = price.split('：')[0]
                value = price.split('：')[1]
                price_dict[name] = value

                # if '纸介版' in price:
                #     price_dict['纸介版'] = price.replace('纸介版：', '')
                # elif '电子版' in price:
                #     price_dict['电子版'] = price.replace('电子版：', '')
                # elif '两个版本' in price:
                #     price_dict['两个版本'] = price.replace('两个版本：', '')

        except Exception:
            return price_dict

        return price_dict



























