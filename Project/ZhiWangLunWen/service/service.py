# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import random
import ast
import json
import hashlib
from lxml import html
from urllib import parse

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


class QiKanLunWen_QiKanTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getFenLeiUrl(self, url):
        fenlei_number = [1, 7]
        for number in fenlei_number:
            # 生成分类列表页url
            fenlei_url = url + 'productcode=CJFD&ClickIndex={}&random={}'.format(number, random.random())
            yield fenlei_url

    def getFenLeiData(self, resp, page):
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        li_list = resp_etree.xpath("//li")
        for li in li_list:
            if li.xpath("./span/a/@title"):
                name1 = li.xpath("./span/a/@title")[0]
                a_list = li.xpath('./dl/dd/a')
                for a in a_list:
                    name2 = a.xpath("./@title")[0]
                    onclick = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                    SearchStateJson = ('{"StateID":"","Platfrom":"","QueryTime":"","Account":"knavi",'
                                       '"ClientToken":"","Language":"","CNode":{"PCode":"CJFD","SMode":"",'
                                       '"OperateT":""},"QNode":{"SelectT":"","Select_Fields":"","S_DBCodes":"",'
                                       '"QGroup":[{"Key":"Navi","Logic":1,"Items":[],'
                                       '"ChildItems":[{"Key":"Journal","Logic":1,"Items":[{"Key":1,"Title":"",'
                                       '"Logic":1,"Name":"%s","Operate":"","Value":"%s?","ExtendType":0,'
                                       '"ExtendValue":"","Value2":""}],"ChildItems":[]}]}],"OrderBy":"OTA|DESC",'
                                       '"GroupBy":"","Additon":""}}' % (
                                           onclick[1], onclick[2]))
                    data = {
                        'SearchStateJson': SearchStateJson,
                        'displaymode': 1,
                        'pageindex': int(page),
                        'pagecount': 21,
                        # 'index': re.findall(r"ClickIndex=(.*?)&", url)[0],
                        'random': random.random()
                    }

                    yield {'column_name': name1 + '_' + name2, 'data': data, 'SearchStateJson': SearchStateJson}

    def getPageNumber(self, resp):
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        if resp_etree.xpath("//em[@class='lblCount']/text()"):
            data_sum = int(resp_etree.xpath("//em[@class='lblCount']/text()")[0])
            if int(data_sum) % 21 == 0:
                page_number = int(int(data_sum) / 21)
                return page_number

            else:
                page_number = int(int(data_sum) / 21) + 1
                return page_number

        else:
            return 0

    def getQiKanLieBiaoPageData(self, SearchStateJson, page):
        data = {
            'SearchStateJson': SearchStateJson,
            'displaymode': 1,
            'pageindex': int(page),
            'pagecount': 21,
            # 'index': re.findall(r"ClickIndex=(.*?)&", url)[0],
            'random': random.random()
        }

        return data

    def getQiKanList(self, resp):
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        li_list = resp_etree.xpath("//ul[@class='list_tup']/li")
        for li in li_list:
            title = li.xpath("./a/@title")[0]
            href = li.xpath("./a/@href")[0]
            pcode = re.findall(r"pcode=(.*?)&", href)[0]
            pykm = re.findall(r"&baseid=(.*)", href)[0]
            url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)

            yield title, url


class HuiYiLunWen_QiKanTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getDaoHangPageData(self):
        data = {
            "productcode": "CIPD",
            "index": "1",
            "random": "0.8249670375543876"
        }

        return data

    # 获取学科导航的最底层导航列表
    def getNavigationList(self, resp):
        return_data = []
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))

        if resp_etree.xpath("//div[@class='guide']"):
            for div in resp_etree.xpath("//div[@class='guide']"):
                if '学科导航' in div.xpath(".//span[@class='wrap']/text()")[0]:
                    li_list = div.xpath(".//ul[@class='contentbox']/li")
                    if li_list:
                        for li in li_list:
                            # 获取'_'前部分栏目名
                            firstname = li.xpath("./span[@class='refirstcol']/a/@title")[0]
                            a_list = li.xpath("./dl[@class='resecondlayer']/dd/a")
                            for a in a_list:
                                save_data = {}
                                # 获取'_'后部分栏目名
                                lastname = a.xpath("./@title")[0]
                                # 生成完整栏目名
                                save_data['lanmu_name'] = firstname + '_' + lastname
                                # 获取栏目url参数
                                save_data['lanmu_url_data'] = re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0]

                                return_data.append(save_data)

        else:
            self.logging.error('学科导航下级导航列表获取失败。')

            return return_data

        return return_data

    # 生成论文集列表页请求参数
    def getLunWenJiUrlData(self, data, page):
        return_data = {}
        SearchStateJson_template = '{"StateID":"","Platfrom":"","QueryTime":"","Account":"knavi","ClientToken":"","Language":"","CNode":{"PCode":"CIPD","SMode":"","OperateT":""},"QNode":{"SelectT":"","Select_Fields":"","S_DBCodes":"","QGroup":[{"Key":"Navi","Logic":1,"Items":[],"ChildItems":[{"Key":"DPaper1","Logic":1,"Items":[{"Key":1,"Title":"","Logic":1,"Name":"168专题代码","Operate":"","Value":"%s?","ExtendType":0,"ExtendValue":"","Value2":""}],"ChildItems":[]}]}],"GroupBy":"","Additon":""}}'
        lanmu_url_data = data['lanmu_url_data']
        lanmu_url_data_dict = ast.literal_eval(lanmu_url_data)
        value = lanmu_url_data_dict[2]
        return_data['SearchStateJson'] = SearchStateJson_template % value
        return_data['displaymode'] = 1
        return_data['pageindex'] = page
        return_data['pagecount'] = 20
        return_data['index'] = 1
        return_data['random'] = random.random()

        return return_data

    # 获取文集数量
    def getHuiYiWenJiNumber(self, resp):
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        if resp_etree.xpath("//em[@class='lblCount']"):
            return re.findall(r"\d+", resp_etree.xpath("//em[@class='lblCount']/text()")[0])[0]

        else:
            return None

    # 生成文集总页数
    def getWenJiPageNumber(self, huiYiWenJi_Number):
        if int(huiYiWenJi_Number) % 20 == 0:
            return int(int(huiYiWenJi_Number) / 20)

        else:
            return int(int(huiYiWenJi_Number) / 20) + 1

    # 获取会议文集种子
    def getWenJiUrlList(self, resp):
        return_data = []
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        if resp_etree.xpath("//div[@class='papersList']/dl"):
            dl_list = resp_etree.xpath("//div[@class='papersList']/dl")
            for dl in dl_list:
                save_data = {}
                url_template = 'http://navi.cnki.net/knavi/DPaperDetail?pcode={}&lwjcode={}&hycode={}'
                url_data = dl.xpath("./dt/a/@href")[0]
                if dl.xpath("./dt/em/text()"):
                    jibie = dl.xpath("./dt/em/text()")[0]
                else:
                    jibie = ""

                # 获取pcode
                if re.findall(r"pcode=(.*?)&", url_data):
                    pcode = re.findall(r"pcode=(.*?)&", url_data)[0]
                elif re.findall(r"pcode=(.*)", url_data):
                    pcode = re.findall(r"pcode=(.*)", url_data)[0]
                else:
                    continue

                # 获取lwjcode
                if re.findall(r"baseid=(.*?),.*", url_data):
                    lwjcode = re.findall(r"baseid=(.*?),.*", url_data)[0]
                elif re.findall(r"baseid=(.*?)&", url_data):
                    lwjcode = re.findall(r"baseid=(.*?)&", url_data)[0]
                elif re.findall(r"baseid=(.*)", url_data):
                    lwjcode = re.findall(r"baseid=(.*)", url_data)[0]
                else:
                    continue

                # 获取hycode
                if re.findall(r"baseid=.*,(.*?)&", url_data):
                    hycode = re.findall(r"baseid=.*,(.*?)&", url_data)[0]
                elif re.findall(r"baseid=.*,(.*)", url_data):
                    hycode = re.findall(r"baseid=.*,(.*)", url_data)[0]
                else:
                    hycode = ''

                save_data['url'] = url_template.format(pcode, lwjcode, hycode)
                save_data['jibie'] = jibie

                return_data.append(save_data)

        else:
            return return_data

        return return_data


class XueWeiLunWen_QiKanTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getIndexUrlData(self):
        data = {
            'productcode': 'CMFD',
            'index': 1,
            'random': random.random()
        }

        return data

    # 获取分类参数
    def getFenLeiDataList(self, resp):
        return_data = []
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        a_list = resp_etree.xpath("//dd/a")
        if a_list:
            for a in a_list:
                onclick = a.xpath("./@onclick")
                if onclick:
                    save_data = re.findall(r"naviSearch(\(.*\));", onclick[0])[0]
                    return_data.append(save_data)

                else:
                    continue
        else:
            return return_data

        return return_data

    # 生成单位列表页参数
    def getDanWeiListUrlData(self, data, page):
        return_data = {}
        data_tuple = ast.literal_eval(data)
        value = data_tuple[2]
        return_data['SearchStateJson'] = json.dumps(
            {"StateID": "", "Platfrom": "", "QueryTime": "", "Account": "knavi", "ClientToken": "",
             "Language": "", "CNode": {"PCode": "CMFD", "SMode": "", "OperateT": ""},
             "QNode": {"SelectT": "", "Select_Fields": "", "S_DBCodes": "", "QGroup": [
                 {"Key": "Navi", "Logic": 1, "Items": [], "ChildItems": [{"Key": "PPaper", "Logic": 1,
                                                                          "Items": [
                                                                              {"Key": 1, "Title": "",
                                                                               "Logic": 1,
                                                                               "Name": "AREANAME",
                                                                               "Operate": "",
                                                                               "Value": "{}?".format(value),
                                                                               "ExtendType": 0,
                                                                               "ExtendValue": "",
                                                                               "Value2": ""}],
                                                                          "ChildItems": []}]}],
                       "OrderBy": "RT|", "GroupBy": "", "Additon": ""}})
        return_data['displaymode'] = 1
        return_data['pageindex'] = page
        return_data['pagecount'] = 21
        return_data['index'] = 1
        return_data['random'] = random.random()

        return return_data

    # 获取单位数量
    def getDanWeiNumber(self, resp):
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        number_data = resp_etree.xpath("//em[@class='lblCount']/text()")
        if number_data:
            return number_data[0]
        else:
            return 0

    # 获取总页数
    def getPageNumber(self, danwei_number):
        if danwei_number % 21 == 0:
            return int(danwei_number / 21)
        else:
            return int((danwei_number / 21) + 1)

    # 获取单位url
    def getDanWeiUrlList(self, resp):
        return_data = []
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        a_list = resp_etree.xpath("//ul[@class='list_tup']/li/a")
        if a_list:
            for a in a_list:
                href = a.xpath("./@href")[0]
                if re.findall(r"pcode=(.*?)&", href):
                    pcode = re.findall(r"pcode=(.*?)&", href)[0]
                elif re.findall(r"pcode=(.*)", href):
                    pcode = re.findall(r"pcode=(.*)", href)[0]
                else:
                    continue

                if re.findall(r"baseid=(.*)", href):
                    logo = re.findall(r"baseid=(.*)", href)[0]
                elif re.findall(r"baseid=(.*?)&", href):
                    logo = re.findall(r"baseid=(.*?)&", href)[0]
                else:
                    continue
                url = 'http://navi.cnki.net/knavi/PPaperDetail?pcode={}&logo={}'.format(pcode, logo)
                return_data.append(url)
        else:
            return return_data

        return return_data


class HuiYiLunWen_LunWenTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 获取pcode、lwjcode
    def getPcodeAndLwjcode(self, data):
        pcode = re.findall(r"pcode=(.*?)&", data)[0]
        lwjcode = re.findall(r"lwjcode=(.*?)&", data)[0]

        return pcode, lwjcode

    # 生成会议数量页url
    def getHuiYiNumberUrl(self, pcode, lwjcode):
        url = 'http://navi.cnki.net/knavi/DpaperDetail/GetDpaperList?pcode={}&lwjcode={}&orderBy=FN&pIdx=0'.format(
            pcode, lwjcode)

        return url

    # 获取会议数量
    def getHuiYiNumber(self, resp):
        response_etree = etree.HTML(resp)
        if response_etree.xpath("//span[@id='partiallistcount']/text()"):
            return int(response_etree.xpath("//span[@id='partiallistcount']/text()")[0])

        else:
            return 0

    # 生成总页数
    def getPageNumber(self, huiyi_number):
        if int(huiyi_number) % 20 == 0:
            return int(int(huiyi_number) / 20)

        else:
            return int((int(huiyi_number) / 20) + 1)

    # 生成会议列表页请求参数
    def getHuiYiListUrlData(self, pcode, lwjcode, page):
        data = {
            'pcode': pcode,
            'lwjcode': lwjcode,
            'orderBy': 'FN|ASC',
            'pIdx': page
        }

        return data

    # 获取会议url
    def getHuiYiUrlList(self, resp):
        return_data = []
        response_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        a_list = response_etree.xpath("//td[@class='nobreak']/following-sibling::td[@class='name']/a")
        for a in a_list:
            href = a.xpath("./@href")[0]
            if href:
                url = 'http://kns.cnki.net/kcms/detail/detail.aspx?' + re.findall(r"\?(.*)", href)[0]
                return_data.append(url)
            else:
                continue

        return return_data


class QiKanLunWen_LunWenTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 生成单个知网期刊的时间列表种子
    def qiKanTimeListUrl(self, url, timelisturl):
        '''
        :param url: 期刊种子
        :return: 时间列表种子
        '''
        # 期刊种子 http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=SHGJ
        # 时间列表种子 http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode=CJFD&pykm=SHGJ&pIdx=0
        try:
            pcode = re.findall(r'pcode=(\w+)&', url)[0]
        except:
            pcode = re.findall(r'pcode=(\w+)', url)[0]

        try:
            pykm = re.findall(r'pykm=(\w+)&', url)[0]
        except:
            pykm = re.findall(r'pykm=(\w+)', url)[0]

        qiKanTimeListUrl = timelisturl.format(pcode, pykm)

        return qiKanTimeListUrl, pcode, pykm

    # 获取期刊【年】、【期】列表
    def getQiKanTimeList(self, resp):
        '''
        :param html: html源码
        :return: 【年】、【期】列表
        '''
        response = resp['data'].content.decode('utf-8')
        return_data = []
        html = bytes(bytearray(response, encoding='utf-8'))
        html_etree = etree.HTML(html)
        try:
            div_list = html_etree.xpath("//div[@class='yearissuepage']")
        except:
            div_list = []
        for div in div_list:
            dl_list = div.xpath("./dl")
            for dl in dl_list:
                time_data = {}
                year = dl.xpath("./dt/em/text()")[0]
                time_data[year] = []
                stage_list = dl.xpath("./dd/a/text()")  # 期列表
                for stage in stage_list:
                    time_data[year].append(stage)
                return_data.append(time_data)

        return return_data

    # 获取论文列表页种子
    def getArticleListUrl(self, url, data, pcode, pykm):
        '''
        :param data: 【年】【期】数据
        :return: 种子列表
        '''
        # 论文列表页种子 http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year=2018&issue=Z1&pykm=SHGJ&pageIdx=0&pcode=CJFD
        return_data = []
        year = str(list(data.keys())[0])
        stage_list = data[year]
        for stages in stage_list:
            stage = re.findall(r'No\.(.*)', stages)[0]
            list_url = url.format(year, stage, pykm, pcode)
            return_data.append(list_url)

        return return_data

    # 获取文章种子列表
    def getArticleUrlList(self, resp, qiKanUrl, xuekeleibie):
        '''
        获取文章种子列表
        :param html: html源码
        :return: 文章种子列表
        '''
        response = resp['data'].content.decode('utf-8')
        return_list = []
        index_url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode='
        html = bytes(bytearray(response, encoding='utf-8'))
        html_etree = etree.HTML(html)
        try:
            dd_list = html_etree.xpath("//dd")
        except:
            dd_list = None
        if dd_list:
            for dd in dd_list:
                href_url = dd.xpath("./span[@class='name']/a/@href")[0]
                # Common/RedirectPage?sfield=FN&dbCode=CJFD&filename=SHGJ2018Z2022&tableName=CJFDPREP&url=
                href_url = re.findall(r"dbCode=(.*?)&url=", href_url)[0]
                url = index_url + href_url
                return_list.append({'url': url, 'qiKanUrl': qiKanUrl, 'xueKeLeiBie': xuekeleibie})
            return return_list

        else:
            return return_list


class XueWeiLunWen_LunWenTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 生成专业列表页请求参数
    def getZhuanYePageData(self, data):
        pcode = re.findall(r"pcode=(.*?)&", data)[0]
        baseID = re.findall(r"logo=(.*)", data)[0]
        url = 'http://navi.cnki.net/knavi/PPaperDetail/GetSubject?pcode={}&baseID={}&scope=%25u5168%25u90E8'.format(
            pcode,
            baseID)

        return url

    # 获取专业列表
    def getZhuanYeList(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        try:
            li_list = resp_etree.xpath("//li[not(@class)]")
        except:
            li_list = []

        for li in li_list:
            if li.xpath("./h1/a/text()"):
                title1 = re.sub(r"\(.*\)", '', li.xpath("./h1/a/text()")[0])
            else:
                continue

            dl_list = li.xpath(".//dl[@class='resecondlayer']")
            for dl in dl_list:
                if dl.xpath(".//b[@class='blue']/@title"):
                    title2 = dl.xpath(".//b[@class='blue']/@title")[0]
                    a_list = dl.xpath(".//a")
                    if a_list:
                        for a in a_list:
                            save_data = {}
                            zhuanYe = ''
                            id = ''
                            if a.xpath("./@title"):
                                title3 = a.xpath("./@title")[0]
                                zhuanYe = title1 + '_' + title2 + '_' + title3
                            if a.xpath("./@id"):
                                id = a.xpath("./@id")[0]

                            if zhuanYe and id:
                                save_data['zhuanYe'] = zhuanYe
                                save_data['zhuanYeId'] = id
                                return_data.append(save_data)
                    else:
                        continue
                else:
                    continue

        return return_data

    # 获取总页数页参数
    def getZhuanYeReqData(self, task, data):
        data = {
            'pcode': re.findall(r"pcode=(.*?)&", task)[0],
            'baseID': re.findall(r"logo=(.*)", task)[0],
            'subCode': data['zhuanYeId'],
            'orderBy': 'RT|DESC',
            'scope': '%u5168%u90E8'
        }

        return data

    # 获取总页数
    def getPageNumber(self, resp):
        resp_etree = etree.HTML(resp)
        page_number = resp_etree.xpath("//span[@id='partiallistcount2']/text()")
        if page_number:
            return page_number[0]
        else:
            return 0

    # 生成论文列表页请求参数
    def getLunWenPageData2(self, task, page, zhuanye_id):
        return_data = {}
        return_data['pcode'] = re.findall(r"pcode=(.*?)&", task)[0]
        return_data['baseID'] = re.findall(r"logo=(.*)", task)[0]
        return_data['subCode'] = zhuanye_id
        return_data['scope'] = '%u5168%u90E8'
        return_data['orderBy'] = 'RT|DESC'
        return_data['pIdx'] = page

        return return_data

    # 获取论文队列参数
    def getLunWenUrlList(self, resp, zhuanye):
        return_data = []
        resp_etree = etree.HTML(bytes(bytearray(resp, encoding='utf-8')))
        try:
            tr_list = resp_etree.xpath("//tr[@class]")
        except:
            tr_list = []
        for tr in tr_list:
            save_data = {}
            td_list = tr.xpath("./td")

            # 获取论文标题
            title_td = td_list[1]
            if title_td.xpath('./a/text()'):
                save_data['title'] = title_td.xpath('./a/text()')[0]
            else:
                save_data['title'] = ''

            # 获取论文作者
            zuozhe_td = td_list[3]
            if zuozhe_td.xpath('./text()'):
                save_data['zuoZhe'] = zuozhe_td.xpath('./text()')[0]
            else:
                save_data['zuoZhe'] = ''

            # 获取论文导师
            daoshi_td = td_list[4]
            if daoshi_td.xpath('./text()'):
                save_data['daoShiXingMing'] = re.sub(r"(;|；)", '|', daoshi_td.xpath('./text()')[0])
            else:
                save_data['daoShiXingMing'] = ''

            # 获取下载次数
            xiazaicishu_td = td_list[8]
            if xiazaicishu_td.xpath('./text()'):
                save_data['xiaZaiCiShu'] = xiazaicishu_td.xpath('./text()')[0]
            else:
                save_data['xiaZaiCiShu'] = 0

            # 获取时间
            shijian_td = td_list[5]
            if shijian_td.xpath('./text()'):
                date = shijian_td.xpath('./text()')[0]
                save_data['shiJian'] = {"v": date, "u": "年"}
            else:
                save_data['shiJian'] = {"v": "", "u": "年"}

            # 获取学位类型
            leixing_td = td_list[6]
            if leixing_td.xpath('./text()'):
                save_data['xueWeiLeiXing'] = leixing_td.xpath('./text()')[0]
            else:
                save_data['xueWeiLeiXing'] = ''

            save_data['zhuanYe'] = zhuanye

            # 获取论文种子
            if title_td.xpath('./a/@href'):
                href = title_td.xpath('./a/@href')
                save_data['url'] = 'http://kns.cnki.net/kcms/detail/detail.aspx?' + re.findall(r"\?(.*)", href[0])[0]
            else:
                save_data['url'] = ''

            return_data.append(save_data)

        return return_data


class QiKanLunWen_LunWenDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取期刊名称
    def getQiKanMingCheng(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            title = html_etree.xpath("//p[@class='title']/a/text()")
        except:
            title = None
        if title:

            return title[0]
        else:

            return ""

    # 判断参考文献类型页面是否正确
    def _judgeHtml(self, divlist, div_number, keyword):
        '''
        :param divlist: div标签列表
        :param div_number: 指定的div标签索引位置
        :param keyword: 判断关键字
        :return:
        '''
        try:
            div = divlist[div_number]
            type_name = div.xpath("./div[@class='dbTitle']/text()")[0]
            if keyword in type_name:

                return True
            else:

                return False
        except:

            return False

    # 获取关联参考文献
    def getGuanLianCanKaoWenXian(self, download_middleware, url):

        return_data = []
        # =================正式============================
        try:
            dbcode = re.findall(r"dbCode=(.*?)&", url)[0]
        except:
            dbcode = re.findall(r"dbCode=(.*)", url)[0]
        try:
            filename = re.findall(r"filename=(.*?)&", url)[0]
        except:
            filename = re.findall(r"filename=(.*)", url)[0]
        try:
            dbname = re.findall(r"tableName=(.*?)&", url)[0]
        except:
            dbname = re.findall(r"tableName=(.*)", url)[0]
        # ================================================
        index_url = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                     'filename={}'
                     '&dbcode={}'
                     '&dbname={}'
                     '&reftype=1'
                     '&catalogId=lcatalog_CkFiles'
                     '&catalogName=')
        # =================开发============================
        # dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        # filename = re.findall(r"filename=(.*?)&", url)[0]
        # dbname = re.findall(r"dbname=(.*)", url)[0]
        # ================================================
        canKaoUrl = index_url.format(filename, dbcode, dbname)
        # 获取参考文献页源码
        canKaoResp = download_middleware.getResp(url=canKaoUrl, mode='get')
        if canKaoResp['status'] == 0:
            response = canKaoResp['data'].content.decode('utf-8')
            html_etree = etree.HTML(response)
            div_list = html_etree.xpath("//div[@class='essayBox']")
            i = -1
            for div in div_list:
                i += 1
                div1_list = div.xpath("./div[@class='dbTitle']")
                for div1 in div1_list:
                    # 获取实体类型
                    shiTiLeiXing = div1.xpath("./text()")[0]
                    # 获取CurDBCode参数
                    CurDBCode = re.findall(r"pc_(.*)", div1.xpath("./b/span/@id")[0])[0]
                    # 获取该类型总页数
                    article_number = int(div1.xpath("./b/span/text()")[0])
                    if article_number % 10 == 0:
                        page_number = int(article_number / 10)
                    else:
                        page_number = int((article_number / 10)) + 1

                    # 题录
                    if '题录' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '题录'
                        # pass
                        # # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data["实体类型"] = "题录"
                                        except:
                                            data["实体类型"] = ""
                                        try:
                                            data["其它信息"] = re.sub(r'\s+', ' ',
                                                                  re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                        except:
                                            data["其他信息"] = ""
                                        try:
                                            data["标题"] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data["标题"] = ""

                                        return_data.append(data)
                            else:
                                continue

                    elif '学术期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学术期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['年卷期'] = ''.join(
                                                re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a[3]/text()")[0]))
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['实体类型'] = '期刊论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            zuoZhe = re.sub(r'\s+', ' ',
                                                            re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                            data['作者'] = re.sub(',', '|', ''.join(re.findall(r'\.(.*?)\.', zuoZhe)))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                                                "./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['刊名'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['刊名'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '国际期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '国际期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '外文文献'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            try:
                                                year = str(re.findall(r"(\d{4})", li.xpath("./text()")[0])[0])
                                            except:
                                                year = ""
                                            try:
                                                qi = str(re.findall(r"(\(.*\))", li.xpath("./text()")[0])[0])
                                            except:
                                                qi = ""
                                            if year and qi:
                                                data['年卷期'] = year + qi
                                            elif year and qi == "":
                                                data['年卷期'] = year
                                            elif year == "" and qi:
                                                data['年卷期'] = year
                                            else:
                                                data['年卷期'] = ""
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['作者'] = re.findall(r'\. (.*) \.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath("./text()")[
                                                                                                     0])))[0]
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath("./a/@href")[0]
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '图书' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '图书'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['实体类型'] = '图书'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            data['其它信息'] = re.sub(r'\s+', ' ', re.sub('.*\[M\]\.', '', ''.join(
                                                re.findall(r"[^&nbsp\r\n]", li.xpath("./text()")[0]))))
                                        except:
                                            data['其他信息'] = ""
                                        try:
                                            data['标题'] = re.findall(r"(.*)\[M\]", re.sub(r'(\r|\n|&nbsp)', '',
                                                                                         li.xpath("./text()")[0]))[0]
                                        except:
                                            data['标题'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '学位' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学位'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                                                "./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '学位论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            re_time = re.compile("\d{4}")
                                            data['时间'] = \
                                                [re.findall(re_time, time)[0] for time in li.xpath(".//text()") if
                                                 re.findall(re_time, time)][0]
                                        except:
                                            data['时间'] = ""
                                        try:
                                            data['作者'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    re.findall(r"\[D\]\.(.*)\.",
                                                                                               li.xpath("./text()")[0])[
                                                                                        0]))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['机构'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['机构'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '标准' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '标准'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标准号'] = ''.join(re.findall(r"[^\r\n]", li.xpath("./text()")[0]))
                                        except:
                                            data['标准号'] = ''
                                        try:
                                            data['标题'] = ''.join(re.findall(r"[^\r\n\.]", li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['时间'] = ''.join(
                                                re.findall(r"[^\r\n\s\.\[S\]]", li.xpath("./text()")[1]))
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '标准'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            url = li.xpath("./a/@href")[0]
                                            # 去掉amp;
                                            url = re.sub('amp;', '', url)
                                            # dbcode替换成dbname
                                            url = re.sub('dbcode', 'dbname', url)
                                            # 截取参数部分
                                            url = re.findall(r"detail\.aspx\?(.*)", url)[0]
                                            # 拼接url
                                            data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?' + url
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '专利' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '专利'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ''
                                        try:
                                            zuozhe = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                      re.sub(r'(\r|\n|&nbsp)', '',
                                                                                             li.xpath('./text()')[0])))[
                                                0]
                                            data['作者'] = re.sub(',', '|', zuozhe)
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['类型'] = re.findall(r'.*\. (.*?)\:', re.sub(r'\s+', ' ',
                                                                                            re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                   li.xpath('./text()')[
                                                                                                       0])))[0]
                                        except:
                                            data['类型'] = ''
                                        try:
                                            data['公开号'] = re.findall('\:(.*?)\,', re.sub(r'\s+', ' ',
                                                                                         re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                li.xpath('./text()')[
                                                                                                    0])))[0]
                                        except:
                                            data['公开号'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '专利'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '报纸' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '报纸'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'.*\.(.*?)\.', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            data['时间'] = re.findall(r'. (\d{4}.*)', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '报纸'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '年鉴' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '年鉴'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['标题'] = re.findall(r'<a onclick="getKns55NaviLink\(.*?\);">(.*)</a>',
                                                                    li_string_html)[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath('./text()')[
                                                                                                     0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['时间'] = \
                                                re.findall(r'<a onclick="getKns55YearNaviLink\(.*?\);">(.*)</a>',
                                                           li_string_html)[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '年鉴'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '会议' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '会议'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = li.xpath("./a/text()")[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['作者'] = re.sub(r"(,|，)", "|", re.findall(r"\[A\]\.(.*?)\.",
                                                                                          re.sub(r"(\r|\n|\s+)", "",
                                                                                                 li.xpath("./text()")[
                                                                                                     0]))[0])
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['文集'] = re.findall(r"\[A\]\..*?\.(.*?)\[C\]",
                                                                    re.sub(r"(\r|\n|\s+)", "",
                                                                           li.xpath("./text()")[0]))[0]
                                        except:
                                            data['文集'] = ''
                                        try:
                                            data['时间'] = {"Y": re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "",li.xpath("./text()")[0]))[0]}
                                        except:
                                            data['时间'] = {}

                                        data['实体类型'] = '会议论文'

                                        return_data.append(data)

                            else:
                                continue

        else:
            self.logging.error('获取参考文献页源码失败，url: {}'.format(canKaoUrl))

        return return_data

    # 获取时间【年】
    def getshiJian(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        p_list = html_etree.xpath("//div[@class='sourinfo']/p")
        if p_list:
            p = p_list[2]
            try:
                shiJian = re.findall(r'(\d{4})年', p.xpath("./a/text()")[0])[0]
            except:
                shiJian = ""

            if shiJian:
                return {"Y": shiJian}

            else:
                shiJian = re.findall(r'(\d{4})年.*期', str(html))
                if shiJian:

                    return {"Y": shiJian[0]}
                else:

                    return {}

    # 获取页数
    def getYeShu(self, resp):
        response = resp['data'].content.decode('utf-8')
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(response))
        if yeShu:

            return {"v": yeShu[0], "u": "页"}
        else:

            return {}

    # 获取关联图书期刊
    def getGuanLianTuShuQiKan(self, qiKanUrl):
        sha1 = hashlib.sha1(qiKanUrl.encode('utf-8')).hexdigest()

        return {"sha": sha1, "ss": "期刊", "url": qiKanUrl}

    # 获取作者
    def getZuoZhe(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='author']/span/a")
        except:
            a_list = None
        name_list = []
        if a_list:
            for a in a_list:
                name = a.xpath("./text()")
                if name:
                    name_list.append(name[0])

            return_data = '|'.join(name_list)

            return return_data
        else:

            return ""

    # 获取文章标题
    def getArticleTitle(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            title = html_etree.xpath("//h2[@class='title']/text()")
        except:
            title = None
        if title:

            return title[0]
        else:

            return ""

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    sfield = url_data[0]
                    skey = parse.quote(url_data[1])
                    code = url_data[2]
                    url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                           'sfield={}&skey={}&code={}'.format(sfield, skey, code))
                    url_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

                    return_data.append({'url': url, 'ss': '机构', 'sha': url_sha1})

            return return_data
        else:

            return return_data

    # 获取PDF下载链接
    def getXiaZai(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            download_url = html_etree.xpath("//a[@id='pdfDown']/@href")
        except:
            download_url = None
        if download_url:

            return ''.join(re.findall(r"[^\n\s']", download_url[0]))
        else:

            return ""

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None
        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '关键词' in title[0]:
                        a_list = p.xpath("./a")
                        for a in a_list:
                            guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;]', a.xpath("./text()")[0]))

                            return_data.append(guanJianCi)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:

            return ''

    # 获取作者单位
    def getZuoZheDanWei(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    zuoZheDanWei = url_data[1]
                    return_data.append(zuoZheDanWei)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:
            return ''

    # 获取大小
    def getDaXiao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None
        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '大小' in title[0]:
                        daXiao = span.xpath("./b/text()")
                        if daXiao:
                            try:
                                v = re.findall(r'\d+', daXiao[0])[0]
                            except:
                                v = ''
                            try:
                                u = re.findall(r"[^\d]", daXiao[0])[0]
                            except:
                                u = 'K'

                            return {'v': v, 'u': u}
                        else:

                            return {}

            return {}
        else:

            return {}

    # 获取在线阅读地址
    def getZaiXianYueDu(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            read_url = html_etree.xpath("//a[@class='icon icon-dlcrsp xml']/@href")
        except:
            read_url = None
        if read_url:

            return 'http://kns.cnki.net' + read_url[0]
        else:

            return ""

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None
        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '分类号' in title[0]:
                        fenLeiHao = p.xpath("./text()")
                        if fenLeiHao:

                            return ''.join(re.sub(';', '|', fenLeiHao[0]))
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取下载次数
    def getXiaZaiCiShu(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None
        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '下载' in title[0]:
                        xiaZaiCiShu = span.xpath("./b/text()")
                        if xiaZaiCiShu:

                            return xiaZaiCiShu[0]

                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取期号
    def getQiHao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='sourinfo']/p")
        except:
            p_list = None
        if p_list:
            p = p_list[2]
            try:
                qiHao = p.xpath("./a/text()")[0]

                return qiHao

            except:
                qiHao = re.findall(r"(\d{4}年.*期)", html)
                if qiHao:

                    return qiHao[0]
                else:

                    return ""
        else:
            return ""

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None
        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '页码' in title[0]:
                        xiaZaiYeMa = span.xpath("./b/text()")
                        if xiaZaiYeMa:

                            return xiaZaiYeMa[0]
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取摘要
    def getZhaiYao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            zhaiYao = html_etree.xpath("//span[@id='ChDivSummary']/text()")
        except:
            zhaiYao = None
        if zhaiYao:

            return zhaiYao[0]
        else:

            return ""

    # 获取基金
    def getJiJin(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None
        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '基金' in title[0]:
                        a_list = p.xpath("./a")
                        if a_list:
                            for a in a_list:
                                guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;；]', a.xpath("./text()")[0]))

                                return_data.append(guanJianCi)

            if return_data:

                return '|'.join(return_data)
            else:

                return return_data
        else:

            return return_data

    # 获取文内图片
    def getZuTo(self, download_middleware, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url, mode='get')
            if image_data_resp['status'] == 0:
                image_data_response = image_data_resp['data'].content.decode('utf-8')
                resp_re = re.findall(r"var oJson={'IDs':(.*)}", image_data_response)
                try:
                    resp_number = len(resp_re[0])
                except:
                    resp_number = 0

                if resp_number > 5:
                    index_list = resp_re[0].split('||')
                    for index in index_list:
                        image_data = {}
                        url_data = re.sub(r"\'", "", re.findall(r"(.*)##", index)[0])
                        image_title = re.sub(r"\'", "", re.findall(r"##(.*)", index)[0])
                        image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                        image_data['url'] = image_url
                        image_data['title'] = image_title
                        image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                        return_data.append(image_data)

                    return return_data

                else:
                    return return_data
            else:
                self.logging.error('图片参数获取失败, url: {}'.format(image_data_url))
                return return_data
        else:
            return return_data

    # 获取doi
    def getDoi(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None
        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if 'DOI' in title[0]:
                        doi = p.xpath("./text()")[0]

                        return doi
            return ""

        else:

            return ""

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='author']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                if not sfield or not skey:
                    return return_data

                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}'
                       '&skey={}'
                       '&code={}'.format(sfield, skey, code))
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
                name = a.xpath("./text()")[0]
                return_data.append({'sha': sha1, 'url': url, 'name': name, 'ss': '人物'})

            return return_data
        else:

            return return_data


class HuiYiLunWen_LunWenDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取标题
    def getArticleTitle(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            title = html_etree.xpath("//h2[@class='title']/text()")
        except:
            title = None

        if title:

            return title[0]
        else:

            return ""

    # 获取作者
    def getZuoZhe(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='author']/span/a")
        except:
            a_list = None
        name_list = []
        if a_list:
            for a in a_list:
                name = a.xpath("./text()")
                if name:
                    name_list.append(name[0])

            return_data = '|'.join(name_list)

            return return_data
        else:

            return ""

    # 获取作者单位
    def getZuoZheDanWei(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    zuoZheDanWei = url_data[1]
                    return_data.append(zuoZheDanWei)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:
            return ''

    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None

        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    sfield = url_data[0]
                    skey = parse.quote(url_data[1])
                    code = url_data[2]
                    url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                           'sfield={}&skey={}&code={}'.format(sfield, skey, code))
                    url_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

                    return_data.append({'url': url, 'ss': '机构', 'sha': url_sha1})

            return return_data
        else:

            return return_data

    # 获取摘要
    def getZhaiYao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            zhaiYao = html_etree.xpath("//span[@id='ChDivSummary']/text()")
        except:
            zhaiYao = None

        if zhaiYao:

            return zhaiYao[0]
        else:

            return ""

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '关键词' in title[0]:
                        a_list = p.xpath("./a")
                        for a in a_list:
                            guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;]', a.xpath("./text()")[0]))

                            return_data.append(guanJianCi)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:

            return ''

    # 获取时间
    def getShiJian(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '会议时间' in title[0]:
                        fenLeiHao = p.xpath("./text()")
                        if fenLeiHao:

                            return ''.join(re.sub(';', '|', fenLeiHao[0]))
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '分类号' in title[0]:
                        fenLeiHao = p.xpath("./text()")
                        if fenLeiHao:

                            return ''.join(re.sub(';', '|', fenLeiHao[0]))
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取文内图片
    def getZuTo(self, download_middleware, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url, mode='get')
            if image_data_resp['status'] == 0:
                image_data_response = image_data_resp['data'].content.decode('utf-8')
                resp_re = re.findall(r"var oJson={'IDs':(.*)}", image_data_response)
                try:
                    resp_number = len(resp_re[0])
                except:
                    resp_number = 0

                if resp_number > 5:
                    index_list = resp_re[0].split('||')
                    for index in index_list:
                        image_data = {}
                        url_data = re.sub(r"\'", "", re.findall(r"(.*)##", index)[0])
                        image_title = re.sub(r"\'", "", re.findall(r"##(.*)", index)[0])
                        image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                        image_data['url'] = image_url
                        image_data['title'] = image_title
                        image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                        return_data.append(image_data)

                    return return_data

                else:
                    return return_data
            else:
                self.logging.error('图片参数获取失败, url: {}'.format(image_data_url))
                return return_data
        else:
            return return_data

    # 获取PDF下载链接
    def getXiaZai(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            download_url = html_etree.xpath("//a[@id='pdfDown']/@href")
        except:
            download_url = None

        if download_url:

            return ''.join(re.findall(r"[^\n\s']", download_url[0]))
        else:

            return ""

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None

        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '页码' in title[0]:
                        xiaZaiYeMa = span.xpath("./b/text()")
                        if xiaZaiYeMa:

                            return xiaZaiYeMa[0]
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取页数
    def getYeShu(self, resp):
        response = resp['data'].content.decode('utf-8')
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(response))
        if yeShu:

            return {"v": yeShu[0], "u": "页"}
        else:

            return {}

    # 获取大小
    def getDaXiao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None

        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '大小' in title[0]:
                        daXiao = span.xpath("./b/text()")
                        if daXiao:
                            try:
                                v = re.findall(r'\d+', daXiao[0])[0]
                            except:
                                v = ''
                            try:
                                u = re.findall(r"[^\d]", daXiao[0])[0]
                            except:
                                u = 'K'

                            return {'v': v, 'u': u}
                        else:

                            return {}

            return {}
        else:

            return {}

    # 获取论文集url
    def getLunWenJiDataUrl(self, resp):
        response = resp['data'].content.decode('utf-8')
        if re.findall(r"RegisterSBlock(\(.*?\));", response):
            try:
                data = ast.literal_eval(re.findall(r"RegisterSBlock(\(.*?\));", response)[0])
                dbcode = data[2]
                dbname = data[1]
                filename = data[0]
                curdbcode = data[3]
                reftype = data[4]
                url = 'http://kns.cnki.net/kcms/detail/frame/asynlist.aspx?dbcode={}&dbname={}&filename={}&curdbcode={}&reftype={}'.format(
                    dbcode,
                    dbname,
                    filename,
                    curdbcode,
                    reftype)
                return url
            except:
                return ''
        else:
            return ''

    # 获取论文集
    def getLunWenJi(self, resp):
        return_data = ''
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        if html_etree.xpath("//div[@class='sourinfo']/p"):
            p_list = html_etree.xpath("//div[@class='sourinfo']/p")
            for p in p_list:
                data = re.sub(r"(\r|\n|\s+|\t)", "", p.xpath("./text()")[0])
                return_data += data
        else:
            return return_data

        return return_data

    # 获取下载次数
    def getXiaZaiCiShu(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None

        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '下载' in title[0]:
                        xiaZaiCiShu = span.xpath("./b/text()")
                        if xiaZaiCiShu:

                            return xiaZaiCiShu[0]

                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取在线阅读地址
    def getZaiXianYueDu(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            read_url = html_etree.xpath("//a[@class='icon icon-dlcrsp xml']/@href")
        except:
            read_url = None

        if read_url:

            return 'http://kns.cnki.net' + read_url[0]
        else:

            return ""

    # 判断参考文献类型页面是否正确
    def _judgeHtml(self, divlist, div_number, keyword):
        '''
        :param divlist: div标签列表
        :param div_number: 指定的div标签索引位置
        :param keyword: 判断关键字
        :return:
        '''
        try:
            div = divlist[div_number]
            type_name = div.xpath("./div[@class='dbTitle']/text()")[0]
            if keyword in type_name:

                return True
            else:

                return False
        except:

            return False

    # 获取关联参考文献
    def getGuanLianCanKaoWenXian(self, download_middleware, url):
        return_data = []
        # =================正式============================
        if re.findall(r"dbcode=(.*?)&", url):
            dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url)[0]
        elif re.findall(r"dbCode=(.*?)&", url):
            dbcode = re.findall(r"dbCode=(.*?)&", url)[0]
        elif re.findall(r"dbCode=(.*)", url):
            dbcode = re.findall(r"dbCode=(.*)", url)[0]
        else:
            return return_data

        if re.findall(r"filename=(.*?)&", url):
            filename = re.findall(r"filename=(.*?)&", url)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url)[0]
        elif re.findall(r"fileName=(.*?)&", url):
            filename = re.findall(r"fileName=(.*?)&", url)[0]
        elif re.findall(r"fileName=(.*)", url):
            filename = re.findall(r"fileName=(.*)", url)[0]
        else:
            return return_data

        if re.findall(r"tableName=(.*?)&", url):
            dbname = re.findall(r"tableName=(.*?)&", url)[0]
        elif re.findall(r"tableName=(.*)", url):
            dbname = re.findall(r"tableName=(.*)", url)[0]
        else:
            return return_data

        # ================================================
        index_url = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                     'filename={}'
                     '&dbcode={}'
                     '&dbname={}'
                     '&reftype=1'
                     '&catalogId=lcatalog_CkFiles'
                     '&catalogName=')
        # =================开发============================
        # dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        # filename = re.findall(r"filename=(.*?)&", url)[0]
        # dbname = re.findall(r"dbname=(.*)", url)[0]
        # ================================================
        canKaoUrl = index_url.format(filename, dbcode, dbname)
        # 获取参考文献页源码
        canKaoResp = download_middleware.getResp(url=canKaoUrl, mode='get')
        if canKaoResp['status'] == 0:
            response = canKaoResp['data'].content.decode('utf-8')
            html_etree = etree.HTML(response)
            div_list = html_etree.xpath("//div[@class='essayBox']")
            i = -1
            for div in div_list:
                i += 1
                div1_list = div.xpath("./div[@class='dbTitle']")
                for div1 in div1_list:
                    # 获取实体类型
                    shiTiLeiXing = div1.xpath("./text()")[0]
                    # 获取CurDBCode参数
                    CurDBCode = re.findall(r"pc_(.*)", div1.xpath("./b/span/@id")[0])[0]
                    # 获取该类型总页数
                    article_number = int(div1.xpath("./b/span/text()")[0])
                    if article_number % 10 == 0:
                        page_number = int(article_number / 10)
                    else:
                        page_number = int((article_number / 10)) + 1

                    # 题录
                    if '题录' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '题录'
                        # pass
                        # # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data["实体类型"] = "题录"
                                        except:
                                            data["实体类型"] = ""
                                        try:
                                            data["其它信息"] = re.sub(r'\s+', ' ',
                                                                  re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                        except:
                                            data["其他信息"] = ""
                                        try:
                                            data["标题"] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data["标题"] = ""

                                        return_data.append(data)
                            else:
                                continue

                    elif '学术期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学术期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['年卷期'] = ''.join(
                                                re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a[3]/text()")[0]))
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['实体类型'] = '期刊论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            zuoZhe = re.sub(r'\s+', ' ',
                                                            re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                            data['作者'] = re.sub(',', '|', ''.join(re.findall(r'\.(.*?)\.', zuoZhe)))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                                                "./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['刊名'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['刊名'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '国际期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '国际期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '外文文献'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            try:
                                                year = str(re.findall(r"(\d{4})", li.xpath("./text()")[0])[0])
                                            except:
                                                year = ""
                                            try:
                                                qi = str(re.findall(r"(\(.*\))", li.xpath("./text()")[0])[0])
                                            except:
                                                qi = ""
                                            if year and qi:
                                                data['年卷期'] = year + qi
                                            elif year and qi == "":
                                                data['年卷期'] = year
                                            elif year == "" and qi:
                                                data['年卷期'] = year
                                            else:
                                                data['年卷期'] = ""
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['作者'] = re.findall(r'\. (.*) \.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath("./text()")[
                                                                                                     0])))[0]
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath("./a/@href")[0]
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '图书' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '图书'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['实体类型'] = '图书'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            data['其它信息'] = re.sub(r'\s+', ' ', re.sub('.*\[M\]\.', '', ''.join(
                                                re.findall(r"[^&nbsp\r\n]", li.xpath("./text()")[0]))))
                                        except:
                                            data['其他信息'] = ""
                                        try:
                                            data['标题'] = re.findall(r"(.*)\[M\]", re.sub(r'(\r|\n|&nbsp)', '',
                                                                                         li.xpath("./text()")[0]))[0]
                                        except:
                                            data['标题'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '学位' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学位'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                                                "./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '学位论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            re_time = re.compile("\d{4}")
                                            data['时间'] = \
                                                [re.findall(re_time, time)[0] for time in li.xpath(".//text()") if
                                                 re.findall(re_time, time)][0]
                                        except:
                                            data['时间'] = ""
                                        try:
                                            data['作者'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    re.findall(r"\[D\]\.(.*)\.",
                                                                                               li.xpath("./text()")[0])[
                                                                                        0]))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['机构'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['机构'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '标准' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '标准'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标准号'] = ''.join(re.findall(r"[^\r\n]", li.xpath("./text()")[0]))
                                        except:
                                            data['标准号'] = ''
                                        try:
                                            data['标题'] = ''.join(re.findall(r"[^\r\n\.]", li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['时间'] = ''.join(
                                                re.findall(r"[^\r\n\s\.\[S\]]", li.xpath("./text()")[1]))
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '标准'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            url = li.xpath("./a/@href")[0]
                                            # 去掉amp;
                                            url = re.sub('amp;', '', url)
                                            # dbcode替换成dbname
                                            url = re.sub('dbcode', 'dbname', url)
                                            # 截取参数部分
                                            url = re.findall(r"detail\.aspx\?(.*)", url)[0]
                                            # 拼接url
                                            data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?' + url
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '专利' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '专利'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ''
                                        try:
                                            zuozhe = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                      re.sub(r'(\r|\n|&nbsp)', '',
                                                                                             li.xpath('./text()')[0])))[
                                                0]
                                            data['作者'] = re.sub(',', '|', zuozhe)
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['类型'] = re.findall(r'.*\. (.*?)\:', re.sub(r'\s+', ' ',
                                                                                            re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                   li.xpath('./text()')[
                                                                                                       0])))[0]
                                        except:
                                            data['类型'] = ''
                                        try:
                                            data['公开号'] = re.findall('\:(.*?)\,', re.sub(r'\s+', ' ',
                                                                                         re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                li.xpath('./text()')[
                                                                                                    0])))[0]
                                        except:
                                            data['公开号'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '专利'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '报纸' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '报纸'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'.*\.(.*?)\.', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            data['时间'] = re.findall(r'. (\d{4}.*)', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '报纸'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '年鉴' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '年鉴'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['标题'] = re.findall(r'<a onclick="getKns55NaviLink\(.*?\);">(.*)</a>',
                                                                    li_string_html)[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath('./text()')[
                                                                                                     0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['时间'] = \
                                                re.findall(r'<a onclick="getKns55YearNaviLink\(.*?\);">(.*)</a>',
                                                           li_string_html)[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '年鉴'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '会议' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '会议'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = li.xpath("./a/text()")[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['作者'] = re.sub(r"(,|，)", "|", re.findall(r"\[A\]\.(.*?)\.",
                                                                                          re.sub(r"(\r|\n|\s+)", "",
                                                                                                 li.xpath("./text()")[
                                                                                                     0]))[0])
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['文集'] = re.findall(r"\[A\]\..*?\.(.*?)\[C\]",
                                                                    re.sub(r"(\r|\n|\s+)", "",
                                                                           li.xpath("./text()")[0]))[0]
                                        except:
                                            data['文集'] = ''
                                        try:
                                            data['时间'] = {"Y": re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "",li.xpath("./text()")[0]))[0]}
                                        except:
                                            data['时间'] = {}

                                        data['实体类型'] = '会议论文'

                                        return_data.append(data)

                            else:
                                continue

        else:
            self.logging.error('获取参考文献页源码失败，url: {}'.format(canKaoUrl))

        return return_data

    # 获取关联活动_会议
    def getGuanLianHuoDong_HuiYi(self, url):
        return_data = {}
        try:
            save_url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?' + re.findall(r"\?(.*)", url)[0]
            return_data['sha'] = hashlib.sha1(save_url.encode('utf-8')).hexdigest()
            return_data['url'] = save_url
            return return_data

        except:
            return return_data


    # 获取关联文集
    def getGuanLianWenJi(self, url):
        return_data = {}
        return_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
        return_data['url'] = url

        return return_data

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            a_list = html_etree.xpath("//div[@class='author']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                if not sfield or not skey:
                    return return_data

                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}'
                       '&skey={}'
                       '&code={}'.format(sfield, skey, code))
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
                name = a.xpath("./text()")[0]
                return_data.append({'sha': sha1, 'url': url, 'name': name, 'ss': '人物'})

            return return_data
        else:

            return return_data


class XueWeiLunWen_LunWenDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取发布单位
    def getFaBuDanWei(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None

        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    zuoZheDanWei = url_data[1]
                    return_data.append(zuoZheDanWei)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:
            return ''

    # 获取摘要
    def getZhaiYao(self, resp):
        html_etree = etree.HTML(resp)
        try:
            zhaiYao = html_etree.xpath("//span[@id='ChDivSummary']/text()")
        except:
            zhaiYao = None
        if zhaiYao:

            return zhaiYao[0]
        else:

            return ""

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '关键词' in title[0]:
                        a_list = p.xpath("./a")
                        for a in a_list:
                            guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;]', a.xpath("./text()")[0]))

                            return_data.append(guanJianCi)

            if return_data:

                return '|'.join(return_data)
            else:

                return ''
        else:

            return ''

    def getJiJin(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '基金' in title[0]:
                        a_list = p.xpath("./a")
                        if a_list:
                            for a in a_list:
                                guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;；]', a.xpath("./text()")[0]))

                                return_data.append(guanJianCi)

            if return_data:

                return '|'.join(return_data)
            else:

                return return_data
        else:

            return return_data

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        html_etree = etree.HTML(resp)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '分类号' in title[0]:
                        fenLeiHao = p.xpath("./text()")
                        if fenLeiHao:

                            return ''.join(re.sub(';', '|', fenLeiHao[0]))
                        else:

                            return ""

            return ""
        else:

            return ""

    # 获取文内图片
    def getZuTo(self, download_middleware, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url, mode='get')
            if image_data_resp['status'] == 0:
                image_data_response = image_data_resp['data'].content.decode('utf-8')
                resp_re = re.findall(r"var oJson={'IDs':(.*)}", image_data_response)
                try:
                    resp_number = len(resp_re[0])
                except:
                    resp_number = 0
                if resp_number > 5:
                    index_list = resp_re[0].split('||')
                    for index in index_list:
                        image_data = {}
                        url_data = re.sub(r"\'", "", re.findall(r"(.*)##", index)[0])
                        image_title = re.sub(r"\'", "", re.findall(r"##(.*)", index)[0])
                        image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                        image_data['url'] = image_url
                        image_data['title'] = image_title
                        image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                        return_data.append(image_data)

                    return return_data
                else:

                    return return_data
            else:
                self.logging.error('图片参数获取失败, url: {}'.format(image_data_url))
                return return_data
        else:
            return return_data

    # 获取页数
    def getYeShu(self, resp):
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(resp))
        if yeShu:

            return {"v": yeShu[0], "u": "页"}
        else:

            return {}

    # 获取大小
    def getDaXiao(self, resp):
        html_etree = etree.HTML(resp)
        try:
            span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        except:
            span_list = None

        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '大小' in title[0]:
                        daXiao = span.xpath("./b/text()")
                        if daXiao:
                            try:
                                v = re.findall(r'\d+', daXiao[0])[0]
                            except:
                                v = ''
                            try:
                                u = re.findall(r"[^\d]", daXiao[0])[0]
                            except:
                                u = 'K'

                            return {'v': v, 'u': u}
                        else:

                            return {}

            return {}
        else:

            return {}

    # 获取下载
    def getXiaZai(self, resp):
        html_etree = etree.HTML(resp)
        try:
            a_list = html_etree.xpath("//div[@class='dllink']/a")
        except:
            a_list = None

        if a_list:
            for a in a_list:
                a_text = a.xpath("./text()")
                if a_text:
                    if '整本下载' in a_text[0]:
                        url = a.xpath("./@href")
                        if url:
                            return url[0]
                        else:
                            continue
                else:
                    continue
        else:
            return ''

    # 获取在线阅读
    def getZaiXianYueDu(self, resp):
        html_etree = etree.HTML(resp)
        try:
            a_list = html_etree.xpath("//div[@class='dllink']/a")
        except:
            a_list = None

        if a_list:
            for a in a_list:
                a_text = a.xpath("./text()")
                if a_text:
                    if '在线阅读' in a_text[0]:
                        url = a.xpath("./@href")
                        if url:
                            return url[0]
                        else:
                            continue
                else:
                    continue
        else:
            return ''

    # 判断参考文献类型页面是否正确
    def _judgeHtml(self, divlist, div_number, keyword):
        '''
        :param divlist: div标签列表
        :param div_number: 指定的div标签索引位置
        :param keyword: 判断关键字
        :return:
        '''
        try:
            div = divlist[div_number]
            type_name = div.xpath("./div[@class='dbTitle']/text()")[0]
            if keyword in type_name:

                return True
            else:

                return False
        except:

            return False

    # 获取关联参考文献
    def getGuanLianCanKaoWenXian(self, download_middleware, url):
        return_data = []
        # =================正式============================
        if re.findall(r"dbcode=(.*?)&", url):
            dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url)[0]
        elif re.findall(r"dbCode=(.*?)&", url):
            dbcode = re.findall(r"dbCode=(.*?)&", url)[0]
        elif re.findall(r"dbCode=(.*)", url):
            dbcode = re.findall(r"dbCode=(.*)", url)[0]
        else:
            return return_data

        if re.findall(r"filename=(.*?)&", url):
            filename = re.findall(r"filename=(.*?)&", url)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url)[0]
        elif re.findall(r"fileName=(.*?)&", url):
            filename = re.findall(r"fileName=(.*?)&", url)[0]
        elif re.findall(r"fileName=(.*)", url):
            filename = re.findall(r"fileName=(.*)", url)[0]
        else:
            return return_data

        if re.findall(r"tableName=(.*?)&", url):
            dbname = re.findall(r"tableName=(.*?)&", url)[0]
        elif re.findall(r"tableName=(.*)", url):
            dbname = re.findall(r"tableName=(.*)", url)[0]
        else:
            return return_data

        # ================================================
        index_url = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                     'filename={}'
                     '&dbcode={}'
                     '&dbname={}'
                     '&reftype=1'
                     '&catalogId=lcatalog_CkFiles'
                     '&catalogName=')
        # =================开发============================
        # dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        # filename = re.findall(r"filename=(.*?)&", url)[0]
        # dbname = re.findall(r"dbname=(.*)", url)[0]
        # ================================================
        canKaoUrl = index_url.format(filename, dbcode, dbname)
        # 获取参考文献页源码
        canKaoResp = download_middleware.getResp(url=canKaoUrl, mode='get')
        if canKaoResp['status'] == 0:
            response = canKaoResp['data'].content.decode('utf-8')
            html_etree = etree.HTML(response)
            div_list = html_etree.xpath("//div[@class='essayBox']")
            i = -1
            for div in div_list:
                i += 1
                div1_list = div.xpath("./div[@class='dbTitle']")
                for div1 in div1_list:
                    # 获取实体类型
                    shiTiLeiXing = div1.xpath("./text()")[0]
                    # 获取CurDBCode参数
                    CurDBCode = re.findall(r"pc_(.*)", div1.xpath("./b/span/@id")[0])[0]
                    # 获取该类型总页数
                    article_number = int(div1.xpath("./b/span/text()")[0])
                    if article_number % 10 == 0:
                        page_number = int(article_number / 10)
                    else:
                        page_number = int((article_number / 10)) + 1

                    # 题录
                    if '题录' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '题录'
                        # pass
                        # # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data["实体类型"] = "题录"
                                        except:
                                            data["实体类型"] = ""
                                        try:
                                            data["其它信息"] = re.sub(r'\s+', ' ',
                                                                  re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                        except:
                                            data["其他信息"] = ""
                                        try:
                                            data["标题"] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data["标题"] = ""

                                        return_data.append(data)
                            else:
                                continue

                    elif '学术期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学术期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['年卷期'] = ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a[3]/text()")[0]))
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['实体类型'] = '期刊论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            zuoZhe = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                            data['作者'] = re.sub(',', '|', ''.join(re.findall(r'\.(.*?)\.', zuoZhe)))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['刊名'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['刊名'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '国际期刊' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '国际期刊'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '外文文献'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            try:
                                                year = str(re.findall(r"(\d{4})", li.xpath("./text()")[0])[0])
                                            except:
                                                year = ""
                                            try:
                                                qi = str(re.findall(r"(\(.*\))", li.xpath("./text()")[0])[0])
                                            except:
                                                qi = ""
                                            if year and qi:
                                                data['年卷期'] = year + qi
                                            elif year and qi == "":
                                                data['年卷期'] = year
                                            elif year == "" and qi:
                                                data['年卷期'] = year
                                            else:
                                                data['年卷期'] = ""
                                        except:
                                            data['年卷期'] = ""
                                        try:
                                            data['作者'] = re.findall(r'\. (.*) \.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath("./text()")[
                                                                                                     0])))[0]
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath("./a/@href")[0]
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '图书' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '图书'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['实体类型'] = '图书'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            data['其它信息'] = re.sub(r'\s+', ' ', re.sub('.*\[M\]\.', '', ''.join(
                                                re.findall(r"[^&nbsp\r\n]", li.xpath("./text()")[0]))))
                                        except:
                                            data['其他信息'] = ""
                                        try:
                                            data['标题'] = re.findall(r"(.*)\[M\]", re.sub(r'(\r|\n|&nbsp)', '',
                                                                                         li.xpath("./text()")[0]))[0]
                                        except:
                                            data['标题'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '学位' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '学位'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                                                "./a[@target='kcmstarget']/text()")[0]))
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '学位论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            re_time = re.compile("\d{4}")
                                            data['时间'] = \
                                            [re.findall(re_time, time)[0] for time in li.xpath(".//text()") if
                                             re.findall(re_time, time)][0]
                                        except:
                                            data['时间'] = ""
                                        try:
                                            data['作者'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    re.findall(r"\[D\]\.(.*)\.",
                                                                                               li.xpath("./text()")[0])[
                                                                                        0]))
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['机构'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                                                    li.xpath("./a[2]/text()")[0]))
                                        except:
                                            data['机构'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '标准' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '标准'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标准号'] = ''.join(re.findall(r"[^\r\n]", li.xpath("./text()")[0]))
                                        except:
                                            data['标准号'] = ''
                                        try:
                                            data['标题'] = ''.join(re.findall(r"[^\r\n\.]", li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['时间'] = ''.join(
                                                re.findall(r"[^\r\n\s\.\[S\]]", li.xpath("./text()")[1]))
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '标准'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            url = li.xpath("./a/@href")[0]
                                            # 去掉amp;
                                            url = re.sub('amp;', '', url)
                                            # dbcode替换成dbname
                                            url = re.sub('dbcode', 'dbname', url)
                                            # 截取参数部分
                                            url = re.findall(r"detail\.aspx\?(.*)", url)[0]
                                            # 拼接url
                                            data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?' + url
                                        except:
                                            data['url'] = ''

                                        return_data.append(data)

                            else:
                                continue

                    elif '专利' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '专利'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ''
                                        try:
                                            zuozhe = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                      re.sub(r'(\r|\n|&nbsp)', '',
                                                                                             li.xpath('./text()')[0])))[
                                                0]
                                            data['作者'] = re.sub(',', '|', zuozhe)
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['类型'] = re.findall(r'.*\. (.*?)\:', re.sub(r'\s+', ' ',
                                                                                            re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                   li.xpath('./text()')[
                                                                                                       0])))[0]
                                        except:
                                            data['类型'] = ''
                                        try:
                                            data['公开号'] = re.findall('\:(.*?)\,', re.sub(r'\s+', ' ',
                                                                                         re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                li.xpath('./text()')[
                                                                                                    0])))[0]
                                        except:
                                            data['公开号'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '专利'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '报纸' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '报纸'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\s+', ' ',
                                                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'.*\.(.*?)\.', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            data['时间'] = re.findall(r'. (\d{4}.*)', re.sub('\s+', ' ',
                                                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                  li.xpath("./text()")[
                                                                                                      0])))[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href')[0]
                                        except:
                                            data['url'] = ''
                                        try:
                                            data['实体类型'] = '报纸'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '年鉴' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '年鉴'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['标题'] = re.findall(r'<a onclick="getKns55NaviLink\(.*?\);">(.*)</a>',
                                                                    li_string_html)[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['机构'] = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                                                          re.sub(r'(\r|\n|&nbsp)', '',
                                                                                                 li.xpath('./text()')[
                                                                                                     0])))[0]
                                        except:
                                            data['机构'] = ''
                                        try:
                                            li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                            data['时间'] = \
                                            re.findall(r'<a onclick="getKns55YearNaviLink\(.*?\);">(.*)</a>',
                                                       li_string_html)[0]
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '年鉴'
                                        except:
                                            data['实体类型'] = ""

                                        return_data.append(data)

                            else:
                                continue

                    elif '会议' in shiTiLeiXing:
                        # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                        keyword = '会议'
                        # pass
                        # 翻页获取
                        for page in range(page_number):
                            qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                                   'filename={}'
                                                   '&dbcode={}'
                                                   '&dbname={}'
                                                   '&reftype=1'
                                                   '&catalogId=lcatalog_CkFiles'
                                                   '&catalogName='
                                                   '&CurDBCode={}'
                                                   '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                            # 获取该页html
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl, mode='get')
                            if leiXingResp['status'] == 0:
                                leiXingResp = leiXingResp['data'].content.decode('utf-8')
                                html_etree = etree.HTML(leiXingResp)
                                leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                                # 判断参考文献类型页面是否正确
                                status = self._judgeHtml(leiXingDivList, i, keyword)
                                if status is True:
                                    leiXingDiv = leiXingDivList[i]
                                    li_list = leiXingDiv.xpath(".//li")
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = li.xpath("./a/text()")[0]
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['作者'] = re.sub(r"(,|，)", "|", re.findall(r"\[A\]\.(.*?)\.",
                                                                                          re.sub(r"(\r|\n|\s+)", "",
                                                                                                 li.xpath("./text()")[
                                                                                                     0]))[0])
                                        except:
                                            data['作者'] = ''
                                        try:
                                            data['文集'] = re.findall(r"\[A\]\..*?\.(.*?)\[C\]",
                                                                    re.sub(r"(\r|\n|\s+)", "",
                                                                           li.xpath("./text()")[0]))[0]
                                        except:
                                            data['文集'] = ''
                                        try:
                                            data['时间'] = {"Y": re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "",li.xpath("./text()")[0]))[0]}
                                        except:
                                            data['时间'] = {}

                                        data['实体类型'] = '会议论文'

                                        return_data.append(data)

                            else:
                                continue

        else:
            self.logging.error('获取参考文献页源码失败，url: {}'.format(canKaoUrl))

        return return_data

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            a_list = html_etree.xpath("//div[@class='author']/span/a")
        except:
            a_list = None
        if a_list:
            for a in a_list:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                if not sfield or not skey:
                    return return_data

                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}'
                       '&skey={}'
                       '&code={}'.format(sfield, skey, code))
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
                name = a.xpath("./text()")[0]
                return_data.append({'sha': sha1, 'url': url, 'name': name, 'ss': '人物'})

            return return_data
        else:

            return return_data

    # 获取关联导师
    def getGuanLianDaoShi(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
        except:
            p_list = None

        if p_list:
            for p in p_list:
                title = p.xpath("./label/text()")
                if title:
                    if '导师' in title[0]:
                        a_list = p.xpath("./a")
                        if a_list:
                            for a in a_list:
                                save_data = {}
                                onclick = ast.literal_eval(
                                    re.findall(r"TurnPageToKnet(\(.*\))", a.xpath("./@onclick")[0])[0])
                                url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                                    onclick[0],
                                    onclick[1],
                                    onclick[2])
                                name = onclick[1]
                                save_data['url'] = url
                                save_data['name'] = name
                                save_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
                                save_data['ss'] = '人物'
                                return_data.append(save_data)

        else:

            return return_data

        return return_data

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        html_etree = etree.HTML(resp)
        try:
            a_list = html_etree.xpath("//div[@class='orgn']/span/a")
        except:
            a_list = None

        if a_list:
            for a in a_list:
                url_data = a.xpath("./@onclick")
                if url_data:
                    url_data = eval(re.findall(r"(\(.*\))", url_data[0])[0])
                    sfield = url_data[0]
                    skey = parse.quote(url_data[1])
                    code = url_data[2]
                    url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                           'sfield={}&skey={}&code={}'.format(sfield, skey, code))
                    url_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

                    return_data.append({'url': url, 'ss': '机构', 'sha': url_sha1})

            return return_data
        else:

            return return_data


class ZhiWangLunWen_JiGouDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取地域
    def getDiyu(self, resp):
        try:
            addr = re.findall(r"<p><label>地域：</label>(.*)</p>", resp)[0]
        except:
            addr = ''

        return addr

    # 获取曾用名
    def getCengYongMing(self, resp):
        try:
            name = re.findall(r"<p><label>曾用名：</label>(.*)</p>", resp)[0]
        except:
            name = ''

        return name

    # 获取官网地址
    def getGuanWangDiZhi(self, resp):
        try:
            url = re.findall(r'<label>官方网址：</label><a target="_blank" href=".*">(.*)</a>', resp)[0]
        except:
            url = ''

        return url

    # 获取机构名
    def getJiGouName(self, resp):
        html_etree = etree.HTML(resp)
        try:
            name = html_etree.xpath("//h2[@class='name']/text()")[0]
        except:
            name = ''

        return name

    # 获取图片
    def getTuPian(self, resp):
        html_etree = etree.HTML(resp)
        try:
            p_list = html_etree.xpath("//div[@class='aboutIntro']/p")
            for p in p_list:
                try:
                    url = p.xpath("./img/@src")[0]
                    return url
                except:
                    continue

            url = ''

            return url
        except:
            url = ''

            return url


class ZhiWangLunWen_ZuoZheDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    def getSuoZaiDanWei(self, resp):
        html_etree = etree.HTML(resp)
        if html_etree.xpath("//p[@class='orgn']/a/text()"):
            company = html_etree.xpath("//p[@class='orgn']/a/text()")[0]
            return re.sub(r'\s+', ' ', re.sub('r(\r|\n|&nbsp)', '', company))

        else:
            return ""

    def getGuanLianQiYeJiGou(self, resp):
        return_data = {}
        html_etree = etree.HTML(resp)
        if html_etree.xpath("//p[@class='orgn']/a/@onclick"):
            company_addr_data = ast.literal_eval(
                re.findall(r"(\(.*\))", html_etree.xpath("//p[@class='orgn']/a/@onclick")[0])[0])
            sfield = company_addr_data[0]
            skey = company_addr_data[1]
            code = company_addr_data[2]
            company_url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(sfield,
                                                                                                             skey,
                                                                                                             code)
            return_data['sha'] = hashlib.sha1(company_url.encode('utf-8')).hexdigest()
            return_data['url'] = company_url
            return_data['ss'] = '机构'

            return return_data

        else:
            return return_data


class ZhiWangLunWen_HuiYiDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):

        return ast.literal_eval(task_data['memo'])

    # 获取字段内容
    def getField(self, resp, text):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//p[@class='hostUnit']"):
            for p in resp_etree.xpath("//p[@class='hostUnit']"):
                if p.xpath("./text()"):
                    if '{}'.format(text) in p.xpath("./text()")[0]:
                        if p.xpath("./span/text()"):
                            return p.xpath("./span/text()")[0]

        return ""


class ZhiWangLunWen_QiKanDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):

        return ast.literal_eval(task_data['memo'])

    def getHeXinShouLu(self, resp):
        return_data = []
        response = bytes(bytearray(resp, encoding='utf-8'))
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

    def getYingWenMingCheng(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            p_text = html_etree.xpath("//dd[@class='infobox']/p[not(@class)]/text()")[0]
            data = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', p_text))

            return data
        except:
            p_text = ''

            return p_text

    def getBiaoShi(self, resp):
        return_data = {}
        response = bytes(bytearray(resp, encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            pic_url = 'http:' + html_etree.xpath("//dt[@id='J_journalPic']/img/@src")[0]
            return_data['sha'] = hashlib.sha1(pic_url.encode('utf-8')).hexdigest()
            return_data['url'] = pic_url
            return return_data

        except:
            return return_data

    def getData(self, resp, text):
        response = bytes(bytearray(resp, encoding='utf-8'))
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

    def getData2(self, resp, text):
        response = bytes(bytearray(resp, encoding='utf-8'))
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

    def getFuHeYingXiangYinZi(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
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

    def getZongHeYingXiangYinZi(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
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

    def getLaiYuanShuJuKu(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            database = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[@class='database']/@title")[0]
        except:
            database = ''

        return database

    def getQiKanRongYu(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            data = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[text()='期刊荣誉：']/following-sibling::p[1]/span/text()")[0]
        except:
            data = ''

        return data.replace(';', '|')


class ZhiWangLunWen_WenJiDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):

        return ast.literal_eval(task_data['memo'])

    def getTitle(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//h3[@class='titbox']/text()"):
            return resp_etree.xpath("//h3[@class='titbox']/text()")[0]

        else:
            return ""

    def getBiaoShi(self, resp):
        return_data = {}
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//img/@src"):
            src = resp_etree.xpath("//img/@src")[0]
            if re.match("http", src):
                return_data['url'] = src
                return_data['sha'] = hashlib.sha1(return_data['url'].encode('utf-8')).hexdigest()

                return return_data
            else:
                return_data['url'] = 'http:' + src
                return_data['sha'] = hashlib.sha1(return_data['url'].encode('utf-8')).hexdigest()

                return return_data
        return return_data

    def getGuanLianHuoDong_HuiYi(self, url):
        return{
            'sha': hashlib.sha1(url.encode('utf-8')).hexdigest(),
            'url': url
        }



    # 获取字段内容
    def getField(self, resp, text):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//p[@class='hostUnit']"):
            for p in resp_etree.xpath("//p[@class='hostUnit']"):
                if p.xpath("./text()"):
                    if '{}'.format(text) in p.xpath("./text()")[0]:
                        if p.xpath("./span/text()"):
                            return p.xpath("./span/text()")[0]

        return ""


class Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getTitle(self, resp):
        '''This is demo'''
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        title = response_etree.xpath("//title/text()")[0]

        return title
