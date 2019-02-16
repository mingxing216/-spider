# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import json
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree

class Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getNid(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        nid = response_etree.xpath("//input[@id='nid']/@value")[0]

        return nid

    def createApiUrl(self, nid, page, count):
        API = 'http://qc.wa.news.cn/nodeart/list?nid={}&pgnum={}&cnt={}&attr=63'.format(
            nid, page, count
        )

        return API

    def getTotal(self, resp, select_num):
        response = resp['data']
        response_content = response.content.decode('utf-8')
        response = re.sub("(\(|\))", '', response_content)
        resp_dict = json.loads(response)
        if resp_dict['status'] == 0:
            # 获取新闻总数
            news_sum = resp_dict['totalnum']
            # 计算总页数
            if news_sum % select_num == 0:

                return int(news_sum / select_num)
            else:

                return int(news_sum / select_num) + 1

        return None

    def getNewsUrlList(self, resp):
        return_data = []
        response = resp['data']
        response_content = response.content.decode('utf-8')
        response = re.sub("(\(|\))", '', response_content)
        resp_dict = json.loads(response)
        if resp_dict['status'] == 0:
            new_data_list = resp_dict['data']['list']
            for new_data in new_data_list:
                data = {}
                if new_data['LinkUrl']:
                    data['new_url'] = new_data['LinkUrl']
                else:
                    data['new_url'] = ""
                if new_data['Abstract']:
                    data['zhaiYao'] = new_data['Abstract']
                else:
                    data['zhaiYao'] = ""
                if new_data['PubTime']:
                    data['faBuShiJian'] = new_data['PubTime']
                else:
                    data['faBuShiJian'] = ""
                if new_data['Title']:
                    data['title'] = new_data['Title']
                else:
                    data['title'] = ""
                try:
                    data['biaoShi'] = new_data['allPics'][0]
                except:
                    data['biaoShi'] = ""

                return_data.append(data)

        return return_data

    def getLaiYuanWangZhan(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//em[@id='source']/text()"):
            return re.sub(r"(\r|\n|&nbsp)", '', response_etree.xpath("//em[@id='source']/text()")[0]).strip()
        elif response_etree.xpath("//span[@class='h-time']/following-sibling::span[1]//text()"):
            return re.sub(r"(\r|\n|&nbsp|来源： )", '',
                          response_etree.xpath("//span[@class='h-time']/following-sibling::span[1]//text()")[0]).strip()
        elif response_etree.xpath("//span[@class='aticle-src']/text()"):
            return re.sub(r"(\r|\n|&nbsp)", '', response_etree.xpath("//span[@class='aticle-src']/text()")[0]).strip()
        else:
            return ''

    def getZhengWen(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//div[@id='p-detail']"):
            zhengWen = etree.tostring(response_etree.xpath("//div[@id='p-detail']")[0], encoding='utf-8').decode('utf-8') + '\n'
            return zhengWen
        else:
            return ''

    def getZhengWen2(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//span[@id='content']"):
            zhengWen = etree.tostring(response_etree.xpath("//span[@id='content']")[0], encoding='utf-8').decode(
                'utf-8') + '\n'
            return zhengWen

        else:
            return ''

    def getZuTu(self, resp, url):
        return_data = []
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        img_template = re.findall(r"http.*\d+-\d+/\d+/", url)
        if img_template:
            url_template = img_template[0]
        else:
            return ""

        if response_etree.xpath("//div[@id='p-detail']"):
            div = response_etree.xpath("//div[@id='p-detail']")[0]
            img_list = div.xpath(".//img/@src")
            for img in img_list:
                if ('.jpg' in img or '.JPG' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.jpg' in img or '.JPG' in img) and re.match(r'http', img):
                    return_data.append(img)
                elif ('.gif' in img or '.GIF' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.gif' in img or '.GIF' in img) and re.match(r'http', img):
                    return_data.append(img)
                elif ('.png' in img or '.PNG' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.png' in img or '.PNG' in img) and re.match(r'http', img):
                    return_data.append(img)
                else:
                    continue

        return return_data

    def getZuTu2(self, resp, url):
        return_data = []
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        img_template = re.findall(r"http.*\d+-\d+/\d+/", url)
        if img_template:
            url_template = img_template[0]
        else:
            return ""

        if response_etree.xpath("//img/@src"):
            img_list = response_etree.xpath("//img/@src")
            for img in img_list:
                if ('.jpg' in img or '.JPG' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.jpg' in img or '.JPG' in img) and re.match(r'http', img):
                    return_data.append(img)
                elif ('.gif' in img or '.GIF' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.gif' in img or '.GIF' in img) and re.match(r'http', img):
                    return_data.append(img)
                elif ('.png' in img or '.PNG' in img) and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif ('.png' in img or '.PNG' in img) and re.match(r'http', img):
                    return_data.append(img)
                else:
                    continue

        return return_data

    def tiHuanTuPian(self, zhengWen, img_url_list):
        return_data = zhengWen
        for img_url in img_url_list:
            try:
                Original_url = re.findall(r'.*\d+-\d+/\d+/(.*\.jpg|.*\.gif|.*\.png|.*\.JPG|.*\.GIF|.*\.PNG)', img_url)[0]
            except:
                continue

            if re.findall(img_url, return_data):
                continue
            else:
                return_data = re.sub(Original_url, img_url, return_data)

        return return_data

    def getNextPageUrl(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//div[@id='div_currpage']/a[text()='下一页']/@href"):
            self.logging.info('获取下一页地址')
            next_page_url = response_etree.xpath("//div[@id='div_currpage']/a[text()='下一页']/@href")[0]

        else:
            next_page_url = None

        return next_page_url

    def getNextPageUrl2(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//a[text()='下一页']/@href"):
            self.logging.info('获取下一页地址')
            next_page_url = response_etree.xpath("//a[text()='下一页']/@href")[0]

        else:
            next_page_url = None

        return next_page_url

    def getBiaoQian(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//meta[@name='keywords']/@content"):
            data = ''.join(response_etree.xpath("//meta[@name='keywords']/@content"))
            return_data = re.sub(r"(,|，)", '|', re.sub(r'(\r|\n)', '', data))

            return return_data.strip()

        else:
            return ''

    def getZeRenBianJi(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//span[@class='p-jc']/text()"):
            data = re.sub(r"(责任编辑:|\r|\n|责任编辑： )", '', ''.join(response_etree.xpath("//span[@class='p-jc']/text()")))

            return data.strip()
        elif response_etree.xpath("//span[@class='editor']/text()"):
            data = re.sub(r"(责任编辑:|\r|\n|责任编辑： |\[|\])", '', ''.join(response_etree.xpath("//span[@class='editor']/text()")))
            return data.strip()
        else:

            return ''

    def getShiPin(self, resp):
        response = resp['data']
        response = response.content.decode('utf-8')
        response_etree = etree.HTML(response)
        if response_etree.xpath("//div[@class='video-url']/text()"):
            data = re.sub(r"(\r|\n|&nbsp)", "", ''.join(response_etree.xpath("//div[@class='video-url']/text()")))

            return data.strip()
        elif response_etree.xpath("//iframe[@class='video-frame']/@src"):
            try:
                data = response_etree.xpath("//iframe[@class='video-frame']/@src")[0]
                return data.strip()

            except:
                return ''

        else:

            return ''