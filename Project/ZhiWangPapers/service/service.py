# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import json
import hashlib
import ast
from lxml import html
from urllib import parse

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


class LunWenServer(object):
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
        div_list = html_etree.xpath("//div[@class='yearissuepage']")
        for div in div_list:
            dl_list = div.xpath("./dl")
            for dl in dl_list:
                time_data = {}
                year = dl.xpath("./dt/em/text()")[0]
                time_data[year] = []
                stage_list = dl.xpath("./dd/a/text()") # 期列表
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
        dd_list = html_etree.xpath("//dd")
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

    # [私有方法]获取关联人物所在公司
    def _getCompany(self, download_middleware, url):
        resp = download_middleware.getResp(url=url)
        if resp['status'] == 0:
            response = resp['data'].content.decode('utf-8')
            html_etree = etree.HTML(response)
            company = html_etree.xpath("//p[@class='orgn']/a/text()")[0]
            # 单位名称
            company = re.sub(r'\s+', ' ', re.sub('r(\r|\n|&nbsp)', '', company))
            # 单位url
            company_addr_data = ast.literal_eval(re.findall(r"(\(.*\))", html_etree.xpath("//p[@class='orgn']/a/@onclick")[0])[0])
            sfield = company_addr_data[0]
            skey = company_addr_data[1]
            code = company_addr_data[2]
            url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(sfield,
                                                                                                           skey,
                                                                                                           code)

            # 主键sha1
            sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

            return {'company_name': company, 'company_url': url, 'company_sha': sha}
        else:

            return []

    # 获取期刊名称
    def getQiKanMingCheng(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        title = html_etree.xpath("//p[@class='title']/a/text()")
        if title:

            return title[0]
        else:

            return ""

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
        canKaoResp = download_middleware.getResp(url=canKaoUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                                            data["其它信息"] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()")[0]))
                                        except:
                                            data["其他信息"] = ""
                                        try:
                                            data["标题"] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()")[0]))
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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
                            leiXingResp = download_middleware.getResp(url=qiKanLunWenIndexUrl)
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

            return {"v":yeShu[0], "u":"页"}
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
        a_list = html_etree.xpath("//div[@class='author']/span/a")
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
        title = html_etree.xpath("//h2[@class='title']/text()")
        if title:

            return title[0]
        else:

            return ""

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        a_list = html_etree.xpath("//div[@class='orgn']/span/a")
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
        download_url = html_etree.xpath("//a[@id='pdfDown']/@href")
        if download_url:

            return ''.join(re.findall(r"[^\n\s']", download_url[0]))
        else:

            return ""

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
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
        a_list = html_etree.xpath("//div[@class='orgn']/span/a")
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
        span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        if span_list:
            for span in span_list:
                title = span.xpath("./label/text()")
                if title:
                    if '大小' in title[0]:
                        daXiao = span.xpath("./b/text()")
                        if daXiao:

                            return {'v': re.findall(r'\d+', daXiao[0])[0], 'u': re.findall(r"[^\d]", daXiao[0])[0]}
                        else:

                            return {}

            return {}
        else:

            return {}

    # 获取在线阅读地址
    def getZaiXianYueDu(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        read_url = html_etree.xpath("//a[@class='icon icon-dlcrsp xml']/@href")
        if read_url:

            return 'http://kns.cnki.net' + read_url[0]
        else:

            return ""

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
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
        span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
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
        p_list = html_etree.xpath("//div[@class='sourinfo']/p")
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

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        span_list = html_etree.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
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
        zhaiYao = html_etree.xpath("//span[@id='ChDivSummary']/text()")
        if zhaiYao:

            return zhaiYao[0]
        else:

            return ""

    # 获取基金
    def getJiJin(self, resp):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
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
    def getWenNeiTuPian(self, download_middleware, resp, url):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url)
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
                        image_data['image_url'] = image_url
                        image_data['image_title'] = image_title
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
        p_list = html_etree.xpath("//div[@class='wxBaseinfo']/p")
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
    def getGuanLianRenWu(self, download_middleware, resp, year):
        return_data = []
        response = resp['data'].content.decode('utf-8')
        html_etree = etree.HTML(response)
        a_list = html_etree.xpath("//div[@class='author']/span/a")
        if a_list:
            for a in a_list:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                if not sfield or not skey or not code:
                    return return_data

                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}'
                       '&skey={}'
                       '&code={}'.format(sfield, skey, code))
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
                name = a.xpath("./text()")[0]
                # 获取人物当前所在单位
                company_data = self._getCompany(download_middleware=download_middleware, url=url)
                if company_data:
                    suoZaiDanWei = {"所在单位": company_data['company_name'], "时间":{"v": year['Y'], "u": "年"},
                                    "单位url": company_data['company_url'], "单位sha1": company_data['company_sha']}

                    return_data.append({'sha': sha1, 'url': url, 'name': name, 'suoZaiDanWei': suoZaiDanWei})
                else:
                    return return_data

            return return_data
        else:

            return return_data


class JiGouServer(object):
    def __init__(self, logging):
        self.logging = logging

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

    def getTitle(self, resp):
        '''This is demo'''
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        title = response_etree.xpath("//title/text()")[0]

        return title