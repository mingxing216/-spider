# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class Server(object):
    def __init__(self, logging):
        self.logging = logging

    # ---------------------
    # task script
    # ---------------------

    # 获取第一分类列表
    def getIndexClassList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        label_list = selector.xpath("//div[@class='leftlist_1']")

        for label in label_list:
            label_id = label.xpath("./@id").extract_first()
            if not label_id:
                continue
            image_id = "{}first".format(label_id)
            lower_url = "http://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
            onclick = label.xpath(".//img[@id='{}']/@onclick".format(image_id)).extract_first()
            if not onclick:
                continue
            try:
                lower_data = ast.literal_eval(re.findall("(\(.*\))", onclick)[0])
                return_data.append(lower_url.format(lower_data[0], lower_data[2]))
            except:
                continue

        return return_data

    # 获取第二分类列表
    def getSecondClassList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        dd_list = selector.xpath("//dd")
        for dd in dd_list:
            lower_url = "http://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
            # 获取code参数
            dd_onclick = dd.xpath("./a/@onclick").extract_first()
            if not dd_onclick:
                continue

            try:
                code = ast.literal_eval(re.findall("(\(.*\))", dd_onclick)[0])[0]
            except:
                code = None
            if not code:
                continue

            # 获取tpinavigroup参数
            image_id = "{}first".format(code)
            img_onclick = dd.xpath(".//img[@id='{}']/@onclick".format(image_id)).extract_first()
            if not img_onclick:
                continue

            try:
                lower_data = ast.literal_eval(re.findall("(\(.*\))", img_onclick)[0])
                return_data.append(lower_url.format(lower_data[0], lower_data[2]))
            except:
                continue

        return return_data

    # 获取第三分类号
    def getCategoryNumber(self, resp):
        return_data = []
        selector = Selector(text=resp)
        dd_list = selector.xpath("//dd")
        for dd in dd_list:
            category = dd.xpath(".//input[@id='selectbox']/@value").extract_first()
            if not category:
                continue
            return_data.append(category)

        return return_data

    # 获取年列表
    def getYearList(self, resp):
        if re.findall(r"<a>(\d+)</a>", resp):
            return re.findall(r"<a>(\d+)</a>", resp)

        else:
            return []

    # 获取url列表
    def getUrlList(self, resp):
        return_data = []
        selector = Selector(text=resp)
        href_list = selector.xpath("//a[@class='fz14']/@href").extract()
        for href in href_list:
            try:
                try:
                    dbcode = re.findall(r"dbcode=(.*?)&", href)[0]
                except:
                    dbcode = re.findall(r"dbcode=(.*)", href)[0]
                try:
                    dbname = re.findall(r"dbname=(.*?)&", href)[0]
                except:
                    dbname = re.findall(r"dbname=(.*)", href)[0]
                try:
                    filename = re.findall(r"filename=(.*?)&", href)[0]
                except:
                    filename = re.findall(r"filename=(.*)", href)[0]

                url = ('http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?'
                       'dbcode={}&'
                       'dbname={}&'
                       'filename={}').format(dbcode, dbname, filename)

                return_data.append(url)
            except:
                continue

        return return_data

    # 获取下一页url
    def getNextUrl(self, resp):
        selector = Selector(text=resp)
        href = selector.xpath("//a[text()='下一页']/@href").extract_first()
        if not href:
            return None
        else:
            next_page = 'http://kns.cnki.net/kns/brief/brief.aspx' + str(href)
            return next_page

    # 替换下一页的页码
    def replace_page_number(self, next_page_url, page):

        return re.sub(r"curpage=\d+", "curpage={}".format(page), next_page_url)