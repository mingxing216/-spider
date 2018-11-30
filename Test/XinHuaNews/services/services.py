# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import json
import base64
import hashlib
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import timeutils

etree = html.etree

class Services(object):
    def __init__(self, logging):
        self.logging = logging

    # 获取新闻来源列表
    def getNewsFromList(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        # 获取新闻来源分类
        news_from_type = resp_etree.xpath("//div[@class='nav-list-wrapper']/h2")
        for from_type in news_from_type:
            try:
                from_type_text = from_type.xpath("./text()")[0]
            except:
                return None
            else:
                if from_type_text == "多语种频道":
                    pass
                else:
                    # 获取分类下的所有新闻来源
                    a_list = from_type.xpath("./following-sibling::ul[1]/li/a")
                    if a_list:
                        for a in a_list:
                            data = {}
                            data['laiYuanTitle'] = a.xpath("./text()")[0]
                            laiYuanUrl = a.xpath("./@href")[0]
                            if re.match(r'http', laiYuanUrl):
                                data['laiYuanUrl'] = laiYuanUrl
                            else:
                                data['laiYuanUrl'] = 'http://m.xinhuanet.com' + re.sub(r"\.\./", "/", laiYuanUrl)
                            return_data.append(data)
                    else:
                        return None

        return return_data

    # 获取新闻来源nid
    def getNewsFromNid(self, resp):
        resp_etree = etree.HTML(resp)
        nid = resp_etree.xpath("//input[@id='nid']/@value")[0]

        return nid

    # 生成新闻列表API
    def createApiUrl(self, nid, page, count):
        API = 'http://qc.wa.news.cn/nodeart/list?nid={}&pgnum={}&cnt={}&attr=63'.format(
            nid, page, count
        )

        return API

    # 获取总页数
    def getPageSum(self, resp, select_num):
        response = re.sub("(\(|\))", '', resp)
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

    # 获取新闻种子列表_模板1、2
    def getNewUrlList(self, resp, one_clazz):
        return_data = []
        response = re.sub("(\(|\))", '', resp)
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
                data['one_clazz'] = one_clazz

                return_data.append(data)

        return return_data

    # 获取新闻种子列表_模板3
    def getNewsUrlList_Template_3(self, resp, one_clazz):
        return_data = []
        resp_etree = etree.HTML(resp)
        url_list = resp_etree.xpath("//li[@class='clearfix']/h3/a/@href")
        for url in url_list:
            data = {}
            data['new_url'] = url
            data['news_from_title'] = one_clazz
            data['last_from_title'] = one_clazz
            return_data.append(data)

        return return_data

    # 获取新闻种子列表_模板4
    def getNewsUrlList_Template_4(self, resp, news_from_title):
        return_data = []
        resp_etree = etree.HTML(resp)
        url_list = resp_etree.xpath("//a[@class='nsl_title']/@href")
        for url in url_list:
            data = {}
            data['new_url'] = url
            data['news_from_title'] = news_from_title
            data['last_from_title'] = news_from_title
            return_data.append(data)

        return return_data

    # 获取栏目分类
    def getColumnTypeList(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        a_list = resp_etree.xpath("//ul[@class='nav2']/li/a")
        for a in a_list:
            data = {}
            try:
                data['shuJuXinWenFenLeiMing'] = a.xpath("./text()")[0]
            except:
                data['shuJuXinWenFenLeiMing'] = ""
            try:
                data['shuJuXinWenFenLeiUrl'] = "http://www.xinhuanet.com/datanews/" + a.xpath("./@href")[0]
            except:
                data['shuJuXinWenFenLeiUrl'] = ""
            return_data.append(data)

        return return_data

    # 获取colNid
    def getColNid(self, resp):
        try:
            colNid = re.findall(r"colNid: \"(.*?)\",", resp)[0]
        except:

            return None

        return colNid

    # 查询思客来源是否含有下一页数据
    def getSiKePageStatus(self, resp):
        resp_dict = json.loads(resp)
        page_html = resp_dict['page']
        if re.findall(r"下一页", page_html):

            return True

        else:

            return False

    # 获取分类pageNid
    def getPageNid(self, resp):
        try:
            pageNid = re.search(r'\"pageNid\":\[\".*?\"\]', str(resp))[0]
        except:
            return None
        else:
            pageNid = re.findall(r"\[\"(.*?)\"\]", pageNid)[0]

            return pageNid

    # 生成数据新闻API
    def createApiUrlForDataNews(self, nid, page):
        API = 'http://qc.wa.news.cn/nodeart/list?nid={}&pgnum={}&cnt=16'.format(
            nid, page
        )

        return API



    def demo(self, **kwargs):
        '''
        html处理 【demo函数， 仅供参考】
        '''
        html = kwargs['html']
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        title = html_etree.xpath("//p[@class='title']/a/text()")
        if title:

            return title[0]
        else:

            return ""


class NewsDataSpiderServices(object):
    def __init__(self, logging):
        self.logging = logging

    # 下载图片
    def downImg(self, download, dao, redis_client, img_url):
        img_resp = download.down_img(redis_client=redis_client, url=img_url)
        img_data_bs64 = base64.b64encode(img_resp)
        # 存储图片
        sha = hashlib.sha1(img_url.encode('utf-8')).hexdigest()
        # LOGGING.info('图片sha: {}'.format(sha))
        item = {
            'pk': sha,
            'type': 'image',
            'url': img_url
        }
        dao.saveImg(media_url=img_url, content=img_data_bs64, type='image', item=item)

    # 获取全部新闻种子数据
    def getUrlDataList(self, filepath):
        return_data = []
        with open(filepath, 'r') as f:
            datas = f.readlines()
        for url_data in datas:
            data_dict = json.loads(url_data)

            return_data.append(data_dict)

        return return_data

    # 模板1——获取来源网站
    def newsTemplate_1_LaiYuanWangZhan(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//em[@id='source']/text()"):
            return re.sub(r"(\r|\n|&nbsp)", '', resp_etree.xpath("//em[@id='source']/text()")[0])
        elif resp_etree.xpath("//span[@class='h-time']/following-sibling::span[1]//text()"):
            return re.sub(r"(\r|\n|&nbsp|来源： )", '', resp_etree.xpath("//span[@class='h-time']/following-sibling::span[1]//text()")[0])
        else:
            return None

    # 模板1——获取正文
    def newsTemplate_1_ZhengWen(self, resp):
        return_data = {}
        resp_etree = etree.HTML(resp)
        page = 1
        while 1:
            # 获取第一页正文
            if resp_etree.xpath("//div[@id='p-detail']"):
                value = etree.tostring(resp_etree.xpath("//div[@id='p-detail']")[0], encoding='utf-8').decode('utf-8')
                return_data['page{}'.format(page)] = value
            else:
                return None
            # 判断是否含有下一页
            if 



    # 模板1——获取标签
    def newsTemplate_1_BiaoQian(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//meta[@name='keywords']/@content"):
            data = ''.join(resp_etree.xpath("//meta[@name='keywords']/@content"))
            return_data = re.sub(r"(,|，)", '|', re.sub(r'(\r|\n)', '', data))

            return return_data

        else:
            return None

    # 模板1——获取组图url列表
    def newsTemplate_1_ZuTu(self, resp, new_url):
        return_data = []
        resp_etree = etree.HTML(resp)
        img_template = re.findall(r"http.*\d+-\d+/\d+/", new_url)
        if img_template:
            url_template = img_template[0]
        else:
            return ""

        if resp_etree.xpath("//div[@id='p-detail']"):
            div = resp_etree.xpath("//div[@id='p-detail']")[0]
            img_list = div.xpath(".//img/@src")
            for img in img_list:
                if '.jpg' in img and not re.match(r'http', img):
                    img_url = url_template + img
                    return_data.append(img_url)
                elif '.jpg' in img and re.match(r'http', img):
                    return_data.append(img)
                else:
                    continue

            return return_data

        else:
            pass

    # 模板1——替换正文中的图片url地址
    def newsTemplate_1_UpdateZhengWen(self, zhengWen, img_url_list):
        return_data = zhengWen
        for img_url in img_url_list:
            # http://www.xinhuanet.com/politics/2018-11/19/1123731745_15425831740051n.jpg
            Original_url = re.findall(r'.*\d+-\d+/\d+/(.*\.jpg)', img_url)[0]
            if re.findall(img_url, return_data):
                continue
            else:
                return_data = re.sub(Original_url, img_url, return_data)

        return return_data

    # 模板1——获取责任编辑
    def newsTemplate_1_ZeRenBianJi(self, resp, url):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//span[@class='p-jc']/text()"):
            data = re.sub(r"(\r|\n|责任编辑： )", '', ''.join(resp_etree.xpath("//span[@class='p-jc']/text()")))

            return data
        elif resp_etree.xpath("//span[@class='editor']/text()"):
            data = re.sub(r"(\r|\n|责任编辑： |\[|\])", '', ''.join(resp_etree.xpath("//span[@class='editor']/text()")))
            return data
        else:

            return None






