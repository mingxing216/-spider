# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import requests
import ast
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


    # ---------------------
    # data script
    # ---------------------

    def getTitle(self, resp):
        selector = Selector(text=resp)
        title_data = selector.xpath("//title/text()").extract_first()
        if title_data:
            return re.sub(r"--国外专利全文数据库", "", title_data)
        else:
            return ''

    def getField(self, resp, text):
        selector = Selector(text=resp)
        field_data = selector.xpath("//td[contains(text(), '{}')]/following-sibling::td[1]/text()".format(text)).extract_first()
        if field_data:
            field =  re.sub(r"(;|；)", "|", re.sub(r"(\r|\n|\t|&nbsp)", "", field_data))
        else:
            field = ""

        return field.strip()

    def getZhuanLiGuoBie(self, gongKaiHao):
        if gongKaiHao:
            guobie = re.search(r".{2}", gongKaiHao).group()
            return guobie

        else:
            return ""

    def getXiaZai(self, resp):
        selector = Selector(text=resp)
        href = selector.xpath(r"//a[contains(text(), '全文下载')]/@href").extract_first()
        if href:
            return 'http://dbpub.cnki.net/grid2008/dbpub/' + href
        else:
            return ""

    def getCookie(self, resp):
        cookies = requests.utils.dict_from_cookiejar(resp.cookies)

        return cookies

    def getPostData(self, response):
        data = ast.literal_eval(re.findall(r"var tzzl_data = ({.*?});", response)[0])

        return data

    def getMorePageUrl(self, resp):
        selector = Selector(text=resp)
        href = selector.xpath("//a[contains(text(), '更多')]/@href").extract_first()
        if href:
            return 'http://dbpub.cnki.net/grid2008/dbpub/' + str(href)
        else:
            return ''

    def getTzzl1(self, resp, save_data):
        selector = Selector(text=resp)
        a_list = selector.xpath("//a")
        for a in a_list:
            data = {}
            title = a.xpath("./text()").extract_first()
            if title == '更多 >>':
                continue
            if title:
                data['title'] = title
            else:
                data['title'] = ''

            href = a.xpath("./@href").extract_first()
            if href:
                data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/' + str(href)
            else:
                data['url'] = ''
            if data not in save_data['guanLianTongZuZhuanLi']:
                save_data['guanLianTongZuZhuanLi'].append(data)

    def getTzzl2(self, resp, save_data):
        selector = Selector(text=resp)

        tr_list = selector.xpath("//table[@class='s_table']/tr")
        tr_number = 0
        if tr_list:
            for tr in tr_list:
                data = {}
                if tr_number == 0:
                    tr_number += 1
                    continue

                title = tr.xpath("./td[2]/a/text()").extract_first()
                if title:
                    data['title'] = title
                else:
                    data['title'] = ''

                href = tr.xpath("./td[2]/a/@href").extract_first()
                if href:
                    data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/' + str(href)
                else:
                    data['url'] = ''
                if data not in save_data['guanLianTongZuZhuanLi']:
                    save_data['guanLianTongZuZhuanLi'].append(data)


    def getNextPage(self, resp):
        selector = Selector(text=resp)
        next_href = selector.xpath("//div[@id='id_grid_turnpage']/a[contains(text(), '下页')]/@href").extract_first()
        if next_href:
            next_page_url = 'http://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + next_href
        else:
            next_page_url = ''

        return next_page_url


