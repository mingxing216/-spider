# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import ast
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

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

    # 获取首页分类列表
    def getIndexClassList(self, resp):
        return_data = []
        response_etree = etree.HTML(resp)
        if response_etree.xpath("//div[@class='leftlist_1']"):
            label_list = response_etree.xpath("//div[@class='leftlist_1']")

            for label in label_list:
                label_id = label.xpath("./@id")[0]
                image_id = "{}first".format(label_id)
                lower_url = "http://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
                lower_data = ast.literal_eval(
                    re.findall("(\(.*\))", label.xpath(".//img[@id='{}']/@onclick".format(image_id))[0])[0]
                )
                return_data.append(lower_url.format(lower_data[0], lower_data[2]))

        return return_data

    # 获取首页分类列表
    def getSecondClassList(self, resp):
        return_data = []
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        dd_list = response_etree.xpath("//dd")
        for dd in dd_list:
            lower_url = "http://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
            # 获取code参数
            code = ast.literal_eval(
                re.findall("(\(.*\))", dd.xpath("./a/@onclick")[0])[0]
            )[0]
            # 获取tpinavigroup参数
            image_id = "{}first".format(code)
            lower_data = ast.literal_eval(
                re.findall("(\(.*\))", dd.xpath(".//img[@id='{}']/@onclick".format(image_id))[0])[0]
            )
            return_data.append(lower_url.format(lower_data[0], lower_data[2]))

        return return_data

    # 获取第三分类号
    def getCategoryNumber(self, resp):
        return_data = []
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        dd_list = response_etree.xpath("//dd")
        for dd in dd_list:
            category = dd.xpath(".//input[@id='selectbox']/@value")[0]
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
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//a[@class='fz14']/@href"):
            href_list = response_etree.xpath("//a[@class='fz14']/@href")
            for href in href_list:
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

        return return_data

    # 获取下一页url
    def getNextUrl(self, resp):
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//a[text()='下一页']/@href"):
            # print('有')
            return 'http://kns.cnki.net/kns/brief/brief.aspx' + response_etree.xpath("//a[text()='下一页']/@href")[0]

        else:
            # print('没有')
            return None

    # 替换下一页的页码
    def replace_page_number(self, next_page_url, page):

        return re.sub(r"curpage=\d+", "curpage={}".format(page), next_page_url)


class DataServer(object):
    def __init__(self, logging):
        self.logging = logging

    @error
    def getTitle(self, resp):
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        try:
            title = re.sub(r"--国外专利全文数据库", "", response_etree.xpath("//title/text()")[0])
        except:
            title = ""

        return title

    @error
    def getField(self, resp, text):
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        try:
            field = re.sub(r"(;|；)", "|", re.sub(r"(\r|\n|\t|&nbsp)", "",
                                                 response_etree.xpath(
                                                     "//td[contains(text(), '{}')]/following-sibling::td[1]/text()".format(
                                                         text))[0]))
        except:
            field = ""

        return field.strip()

    def getZhuanLiGuoBie(self, gongKaiHao):
        if gongKaiHao:
            guobie = re.search(r".{2}", gongKaiHao).group()
            return guobie

        else:
            return ""

    @error
    def getXiaZai(self, resp):
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//a[contains(text(), '全文下载')]/@href"):
            url = 'http://dbpub.cnki.net/grid2008/dbpub/' + response_etree.xpath("//a[contains(text(), '全文下载')]/@href")[0]
            return url

        else:
            return ""
        
    @error
    def getYcTzzlData(self, resp):
        return_data = []
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        tr_list = response_etree.xpath("//table[@class='s_table']/tr")
        tr_number = 0
        if tr_list:
            for tr in tr_list:
                data = {}
                if tr_number == 0:
                    tr_number += 1
                    continue
                data['title'] = tr.xpath("./td[2]/a/text()")[0]
                data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/' + tr.xpath("./td[2]/a/@href")[0]
                if data not in return_data:
                    return_data.append(data)

        return return_data

    @error
    def getYctzzlNextPage(self, resp):
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//a[contains(text(), '下页')]/@href"):
            return 'http://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + response_etree.xpath("//a[contains(text(), '下页')]/@href")[0]

        else:
            return ''



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
