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

    # ====== 专利实体
    def getTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title_data = selector.xpath("//title/text()").extract_first()
            title = re.sub(r"--中国专利全文数据库", "", title_data).strip()
        except Exception:
            title = ""

        return title

    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            field_data = selector.xpath("//td[contains(text(), '{}')]/following-sibling::td[1]/text()".format(para)).extract_first()
            field_value =  re.sub(r"(;|；)", "|", re.sub(r"(\r|\n|\t)", "", field_data)).strip()
        except Exception:
            field_value = ""

        return field_value

    def getHtml(self, html, para):
        tree = etree.HTML(html)
        try:
            tag = tree.xpath("//td[contains(text(), '{}')]/following-sibling::td[1]".format(para))[0]
            html_value = re.sub(r"[\n\r\t]", "", tostring(tag).decode('utf-8')).strip()

        except Exception:
            html_value = ""

        return html_value

    def getXiaZai(self, resp):
        selector = Selector(text=resp)
        try:
            href = selector.xpath("//a[contains(text(), '下载')]/@href").extract_first()
            link = 'https://dbpub.cnki.net/grid2008/dbpub/' + href
        except Exception:
            link = ""

        return link

    def getZhuanLiGuoBie(self, gongKaiHao):
        if gongKaiHao:
            # guobie = re.match(r".{2}", gongKaiHao).group()
            guobie = gongKaiHao[:2]
            return guobie

        else:
            return ""

    def getGongGao(self, resp):
        selector = Selector(text=resp)
        try:
            href = selector.xpath("//a[contains(text(), '查询法律状态')]/@href").extract_first().replace('http', 'https')
        except Exception:
            href = ""

        return href

    # ====== 公告实体
    # 公告标题
    def getTitles(self, resp):
        selector = Selector(text=resp)
        try:
            nodes = selector.xpath("//table/thead/tr/th/text()").extract()
        except Exception:
            nodes = ""

        return nodes

    # 公告标签
    def getGongGaoNodes(self, resp):
        selector = Selector(text=resp)
        try:
            nodes = selector.xpath("//table/tr[position()<last()]")
        except Exception:
            nodes = ""

        return nodes

    # 法律状态公告日
    def getGongGaoInfo(self, node, i):
        try:
            gonggao = node.xpath("./td[{}]/text()".format(i+1)).extract_first()
            gonggao_value = re.sub(r"[\n\r\t]", " ", gonggao).strip()
        except Exception:
            gonggao_value = ""

        return gonggao_value

    # 申请号
    def getShenQingHao(self, resp):
        selector = Selector(text=resp)
        try:
            shenqinghao = re.sub(r"申 请 号[：:]", "", selector.xpath("//h3/text()").extract_first().strip())
        except Exception:
            shenqinghao = ""

        return shenqinghao

    # 关联专利
    def guanLianZhuanLi(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '专利'
        except Exception:
            return e

        return e


    def getNextPage(self, resp):
        selector = Selector(text=resp)
        next_href = selector.xpath("//div[@id='id_grid_turnpage']/a[contains(text(), '下页')]/@href").extract_first()
        if next_href:
            next_page_url = 'https://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + next_href
        else:
            next_page_url = ''

        return next_page_url



























