# -*-coding:utf-8-*-
import sys
import os
import re
import pprint
import time
import hashlib
from lxml import html
from urllib import parse

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from utils import redis_dbutils
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider

etree = html.etree

class zhiwangPeriodocalService(object):
    def __init__(self):
        pass

    def getColumnNumber(self, html):
        '''
        获取根栏目数量
        :param html: html源码
        :return: 根栏目数量
        '''
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        column_number = 0
        div_list = html_etree.xpath("//div[@class='guide']")
        for div in div_list:
            column_number += 1

        return column_number

    def getColumnSunData(self, html):
        '''
        获取最底层栏目请求参数
        :param html: 根栏目源码
        :return: 数据集合
        '''
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        li_list = html_etree.xpath("//li")
        for li in li_list:
            column_name = li.xpath("./span[@class='refirstcol']/a/@title")[0]
            dd_list = li.xpath("./dl[@class='resecondlayer']/dd")
            for dd in dd_list:
                data = {}
                data['column_name'] = column_name + '_' + dd.xpath("./a/@title")[0]
                onclick_data = dd.xpath("./a/@onclick")[0]
                data_tuple = re.findall(r"(\(.*\))", onclick_data)[0]  # 数据元祖
                data_tuple = "(" + ''.join(re.findall(r"[^()]", data_tuple)) + ")"
                try:
                    data_tuple = eval(data_tuple)
                    data['name'] = data_tuple[1]
                    data['value'] = data_tuple[2]
                    data['has_next'] = True
                    return_data.append(data)
                except:

                    continue

        return return_data

    def createTaskQueue(self, html, column_name, redis_name, redis_name2):
        '''
        生成期刊主页任务队列， 获取总期刊数
        :param html: 期刊列表页源码
        :return: 总期刊数
        '''
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        if html_etree is None:
            with open('none.html', 'w') as f:
                f.write(str(html))
        li_list = html_etree.xpath("//ul[@class='list_tab']/li")
        i = 0
        for li in li_list:
            queue_data = {}
            if i == 0:
                i += 1
                continue
            title = li.xpath("./span[@class='tab_1']/h2/a/text()")[0]
            href = li.xpath("./span[@class='tab_1']/h2/a/@href")[0]
            pcode = re.findall(r"pcode=(.*?)&", href)[0]
            pykm = re.findall(r"&baseid=(.*)", href)[0]
            url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)
            queue_data["column_name"] = column_name
            queue_data["title"] = title
            queue_data["url"] = url
            # 生成期刊文章对应的期刊url队列
            redis_dbutils.saveSet(redis_name, queue_data)
            # 生成期刊抓取任务队列
            redis_dbutils.saveSet(redis_name2, queue_data)
        # 总期刊数
        qikan_number = re.findall(r"(\d+)", html_etree.xpath("//div[@class='pagenav']/text()")[0])[0]

        return qikan_number

    def qiKanTimeListUrl(self, url, timelisturl):
        '''
        生成单个知网期刊的时间列表种子
        :param url: 期刊种子
        :return: 时间列表种子
        '''
        # 期刊种子 http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=SHGJ
        # 时间列表种子 http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode=CJFD&pykm=SHGJ&pIdx=0
        pcode = re.findall(r'pcode=(\w+)&', url)[0]
        pykm = re.findall(r'pykm=(\w+)', url)[0]
        qiKanTimeListUrl = timelisturl.format(pcode, pykm)

        return qiKanTimeListUrl, pcode, pykm

    def getQiKanTimeList(self, html):
        '''
        获取期刊【年】、【期】
        :param html: html源码
        :return: 【年】、【期】列表
        '''
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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

    def getArticleListUrl(self, data, pcode, pykm):
        '''
        获取文章列表页种子
        :param data: 【年】【期】数据
        :return: 种子列表
        '''
        # 文章列表页种子 http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year=2018&issue=Z1&pykm=SHGJ&pageIdx=0&pcode=CJFD
        return_data = []
        url = 'http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'
        year = str(list(data.keys())[0])
        stage_list = data[year]
        for stages in stage_list:
            stage = re.findall(r'No\.(.*)', stages)[0]
            list_url = url.format(year, stage, pykm, pcode)
            return_data.append(list_url)

        return return_data

    def getArticleUrlList(self, html, qiKanUrl, xuekeleibie):
        '''
        获取文章种子列表
        :param html: html源码
        :return: 文章种子列表
        '''
        return_list = []
        index_url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode='
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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

    # 获取期刊名称
    def getQiKanMingCheng(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        title = html_etree.xpath("//p[@class='title']/a/text()")
        if title:

            return title[0]
        else:

            return ""

    # 获取关联参考文献
    def getGuanLianCanKaoWenXian(self, url):
        return_data = []
        # 爬虫对象
        spider = zhiwang_periodical_spider.SpiderMain()

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
        canKaoHtml = spider.getRespForGet(url=canKaoUrl)
        resp = bytes(bytearray(canKaoHtml, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data["实体类型"] = "题录"
                                        except:
                                            data["实体类型"] = ""
                                        try:
                                            data["其它信息"] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[0])
                                        except:
                                            data["其他信息"] = ""
                                        try:
                                            data["标题"] = re.sub(r'\r\n\s*', '', li.xpath("./a/text()")[0])
                                        except:
                                            data["标题"] = ""

                                        return_data.append(data)
                                    break

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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
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
                                            data['作者'] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[0])
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['标题'] = re.sub(r'\r\n\s*', '', li.xpath("./a[@target='kcmstarget']/text()")[0])
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['刊名'] = re.sub(r'\r\n\s*', '', li.xpath("./a[2]/text()")[0])
                                        except:
                                            data['刊名'] = ""

                                        return_data.append(data)
                                    break
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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\r\n\s*', '', li.xpath("./a/text()")[0])
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

                                        #TODO 作者和刊名无法区分

                                        return_data.append(data)
                                    break
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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['实体类型'] = '图书'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            data['其它信息'] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[0])
                                        except:
                                            data['其他信息'] = ""
                                        try:
                                            data['标题'] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[0])
                                        except:
                                            data['标题'] = ""

                                        return_data.append(data)
                                    break

                            else:
                                continue

                elif '学位' in shiTiLeiXing:
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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标题'] = re.sub(r'\r\n\s*', '', li.xpath("./a[@target='kcmstarget']/text()")[0])
                                        except:
                                            data['标题'] = ""
                                        try:
                                            data['实体类型'] = '学位论文'
                                        except:
                                            data['实体类型'] = ""
                                        try:
                                            re_time = re.compile("\d{4}")
                                            data['时间'] = [re.findall(re_time, time)[0] for time in li.xpath(".//text()") if re.findall(re_time, time)][0]
                                        except:
                                            data['时间'] = ""
                                        try:
                                            data['作者'] = re.sub(r'\r\n\s*', '', re.findall(r"\[D\]\.(.*)\.", li.xpath("./text()")[0])[0])
                                        except:
                                            data['作者'] = ""
                                        try:
                                            data['机构'] = re.sub(r'\r\n\s*', '', li.xpath("./a[2]/text()")[0])
                                        except:
                                            data['机构'] = ""

                                        return_data.append(data)
                                    break

                            else:
                                continue

                elif '标准' in shiTiLeiXing:
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
                        for get_number in range(20):
                            # 获取该页html
                            leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                            leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                            html_etree = etree.HTML(leiXingResp)
                            leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                            # 判断参考文献类型页面是否正确
                            status = self._judgeHtml(leiXingDivList, i, keyword)
                            if status is True:
                                leiXingDiv = leiXingDivList[i]
                                li_list = leiXingDiv.xpath(".//li")
                                if li_list:
                                    for li in li_list:
                                        data = {}
                                        try:
                                            data['标准号'] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[0])
                                        except:
                                            data['标准号'] = ''
                                        try:
                                            data['标题'] = re.sub(r'\r\n\s*', '', li.xpath("./a/text()")[0])
                                        except:
                                            data['标题'] = ''
                                        try:
                                            data['时间'] = re.sub(r'\r\n\s*', '', li.xpath("./text()")[1])
                                        except:
                                            data['时间'] = ''
                                        try:
                                            data['实体类型'] = '标准类型'
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
                                    break

                            else:
                                continue

        return return_data

    # 获取关联引证文献
    def getGuanLianYinZhengWenXian(self, url):
        return_data = []
        # 爬虫对象
        spider = zhiwang_periodical_spider.SpiderMain()

        # =================正式============================
        # dbcode = re.findall(r"dbCode=(.*?)&", url)[0]
        # filename = re.findall(r"filename=(.*?)&", url)[0]
        # dbname = re.findall(r"tableName=(.*)", url)[0]
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
                     '&reftype=3'
                     '&catalogId=lcatalog_YzFiles'
                     '&catalogName=')
        # =================开发============================
        # dbcode = ''.join(re.sub('&', '', re.findall(r"dbcode=(.*?)", url)[0]))
        # filename = ''.join(re.sub('&', '', re.findall(r"filename=(.*?)", url)[0]))
        # dbname = ''.join(re.sub('&', '', re.findall(r"dbname=(.*)", url)[0]))
        # ================================================
        canKaoUrl = index_url.format(filename, dbcode, dbname)
        # 获取参考文献页源码
        canKaoHtml = spider.getRespForGet(url=canKaoUrl)
        resp = bytes(bytearray(canKaoHtml, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
                    # pass
                    # 翻页获取
                    for page in range(page_number):
                        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                               'filename={}'
                                               '&dbcode={}'
                                               '&dbname={}'
                                               '&reftype=3'
                                               '&catalogId=lcatalog_YzFiles'
                                               '&catalogName='
                                               '&CurDBCode={}'
                                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                        # 获取该页html
                        leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                        leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                        html_etree = etree.HTML(leiXingResp)
                        leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                        if leiXingDivList:
                            leiXingDiv = leiXingDivList[i]
                            li_list = leiXingDiv.xpath(".//li")
                            if li_list:
                                for li in li_list:
                                    data = {}
                                    try:
                                        data['实体类型'] = '题录'
                                    except:
                                        data['实体类型'] = ""
                                    try:
                                        data['其它信息'] = ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./text()")[0]))
                                    except:
                                        data['其他信息'] = ""
                                    try:
                                        data['标题'] = ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a/text()")[0]))
                                    except:
                                        data['标题'] = ""

                                    return_data.append(data)

                elif '学术期刊' in shiTiLeiXing:
                    # pass
                    # 翻页获取
                    for page in range(page_number):
                        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                               'filename={}'
                                               '&dbcode={}'
                                               '&dbname={}'
                                               '&reftype=3'
                                               '&catalogId=lcatalog_YzFiles'
                                               '&catalogName='
                                               '&CurDBCode={}'
                                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                        # 获取该页html
                        leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                        leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                        html_etree = etree.HTML(leiXingResp)
                        leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                        if leiXingDivList:
                            leiXingDiv = leiXingDivList[i]
                            li_list = leiXingDiv.xpath(".//li")
                            if li_list:
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
                                        data['作者'] = ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./text()")[0]))
                                    except:
                                        data['作者'] = ""
                                    try:
                                        data['标题'] = li.xpath("./a[@target='kcmstarget']/text()")[0]
                                    except:
                                        data['标题'] = ""
                                    try:
                                        data['刊名'] = li.xpath("./a[2]/text()")[0]
                                    except:
                                        data['刊名'] = ""

                                    return_data.append(data)

                elif '国际期刊' in shiTiLeiXing:
                    # pass
                    # 翻页获取
                    for page in range(page_number):
                        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                               'filename={}'
                                               '&dbcode={}'
                                               '&dbname={}'
                                               '&reftype=3'
                                               '&catalogId=lcatalog_YzFiles'
                                               '&catalogName='
                                               '&CurDBCode={}'
                                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                        # 获取该页html
                        leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                        leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                        html_etree = etree.HTML(leiXingResp)
                        leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                        if leiXingDivList:
                            leiXingDiv = leiXingDivList[i]
                            li_list = leiXingDiv.xpath(".//li")
                            if li_list:
                                for li in li_list:
                                    data = {}
                                    try:
                                        data['标题'] = ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a/text()")[0]))
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

                                    # TODO 作者和刊名无法区分

                                    return_data.append(data)

                elif '图书' in shiTiLeiXing:
                    # pass
                    # 翻页获取
                    for page in range(page_number):
                        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                               'filename={}'
                                               '&dbcode={}'
                                               '&dbname={}'
                                               '&reftype=3'
                                               '&catalogId=lcatalog_YzFiles'
                                               '&catalogName='
                                               '&CurDBCode={}'
                                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                        # 获取该页html
                        leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                        leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                        html_etree = etree.HTML(leiXingResp)
                        leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                        if leiXingDivList:
                            leiXingDiv = leiXingDivList[i]
                            li_list = leiXingDiv.xpath(".//li")
                            if li_list:
                                for li in li_list:
                                    data = {}
                                    try:
                                        data['实体类型'] = '图书'
                                    except:
                                        data['实体类型'] = ""
                                    try:
                                        data['其它信息'] = re.sub('.*\[M\]\.', '',
                                                              ''.join(re.findall(r"[^&nbsp\r\n\s]", li.xpath("./text()")[0])))
                                    except:
                                        data['其他信息'] = ""
                                    try:
                                        data['标题'] = re.findall(r"(.*)\[M\]", ''.join(
                                            re.findall(r"[^&nbsp\r\n\s]", li.xpath("./text()")[0])))[0]
                                    except:
                                        data['标题'] = ""

                                    return_data.append(data)

                elif '学位' in shiTiLeiXing:
                    # pass
                    # 翻页获取
                    for page in range(page_number):
                        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                               'filename={}'
                                               '&dbcode={}'
                                               '&dbname={}'
                                               '&reftype=3'
                                               '&catalogId=lcatalog_YzFiles'
                                               '&catalogName='
                                               '&CurDBCode={}'
                                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
                        # 获取该页html
                        leiXingResp = spider.getRespForGet(url=qiKanLunWenIndexUrl)
                        leiXingResp = bytes(bytearray(leiXingResp, encoding='utf-8'))
                        html_etree = etree.HTML(leiXingResp)
                        leiXingDivList = html_etree.xpath("//div[@class='essayBox']")
                        if leiXingDivList:
                            leiXingDiv = leiXingDivList[i]
                            li_list = leiXingDiv.xpath(".//li")
                            if li_list:
                                for li in li_list:
                                    data = {}
                                    try:
                                        data['标题'] = ''.join(
                                            re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a[@target='kcmstarget']/text()")[0]))
                                    except:
                                        data['标题'] = ""
                                    try:
                                        data['实体类型'] = '学位论文'
                                    except:
                                        data['实体类型'] = ""
                                    try:
                                        re_time = re.compile("\d{4}")
                                        data['时间'] = [re.findall(re_time, time)[0] for time in li.xpath(".//text()") if
                                                      re.findall(re_time, time)][0]
                                    except:
                                        data['时间'] = ""
                                    try:
                                        data['作者'] = ''.join(
                                            re.findall(r"[^\s]", re.findall(r"\[D\]\.(.*)\.", li.xpath("./text()")[0])[0]))
                                    except:
                                        data['作者'] = ""
                                    try:
                                        data['机构'] = li.xpath("./a[2]/text()")[0]
                                    except:
                                        data['机构'] = ""

                                    return_data.append(data)


        return return_data

    # 获取时间【年】
    def getshiJian(self, html):
        # shiJian = re.findall(r'(\d{4})年.*期', str(html))
        # if shiJian:
        #
        #     return {"Y": shiJian[0]}
        # else:
        #
        #     return {}
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getYeShu(self, html):
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(html))
        if yeShu:

            return {"v":yeShu[0], "u":"页"}
        else:

            return {}

    # 获取关联图书期刊
    def getGuanLianTuShuQiKan(self, qiKanUrl):
        sha1 = hashlib.sha1(qiKanUrl.encode('utf-8')).hexdigest()

        return {"sha": sha1, "ss": "期刊", "url": qiKanUrl}

    # 获取作者
    def getZuoZhe(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getArticleTitle(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        title = html_etree.xpath("//h2[@class='title']/text()")
        if title:

            return title[0]
        else:

            return ""

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, html):
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getXiaZai(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        download_url = html_etree.xpath("//a[@id='pdfDown']/@href")
        if download_url:

            return ''.join(re.findall(r"[^\n\s']", download_url[0]))
        else:

            return ""

    # 获取关键词
    def getGuanJianCi(self, html):
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getZuoZheDanWei(self, html):
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getDaXiao(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getZaiXianYueDu(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        read_url = html_etree.xpath("//a[@class='icon icon-dlcrsp xml']/@href")
        if read_url:

            return 'http://kns.cnki.net' + read_url[0]
        else:

            return ""

    # 获取分类号
    def getZhongTuFenLeiHao(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getXiaZaiCiShu(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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

    # 获取关联人物
    def getGuanLianRenWu(self, html):
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        a_list = html_etree.xpath("//div[@class='author']/span/a")
        if a_list:
            for a in a_list:
                url_data = eval(re.findall(r"(\(.*\))", a.xpath("./@onclick")[0])[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}'
                       '&skey={}'
                       '&code={}'.format(sfield, skey, code))
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
                name = a.xpath("./text()")[0]

                return_data.append({'sha': sha1, 'ss': '人物', 'url': url, 'name': name})

            return return_data
        else:

            return return_data

    # 获取期号
    def getQiHao(self, html):
        # qiHao = re.findall(r"(\d{4}年.*期)", html)
        # if qiHao:
        #
        #     return qiHao[0]
        # else:
        #
        #     return ""
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getSuoZaiYeMa(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getZhaiYao(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        zhaiYao = html_etree.xpath("//span[@id='ChDivSummary']/text()")
        if zhaiYao:

            return zhaiYao[0]
        else:

            return ""

    # 获取基金
    def getJiJin(self, html):
        return_data = []
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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
    def getWenNeiTuPian(self, html, url):
        # 爬虫对象
        spider = zhiwang_periodical_spider.SpiderMain()
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            page_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            resp = spider.getRespForGet(url=page_data_url)
            resp = re.findall(r"var oJson={'IDs':(.*)}", resp)
            # resp = eval(re.findall(r'var oJson=({.*})', resp)[0])['IDs']
            if resp:
                sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

                return {"sha": sha1, "url": url, "ss": "组图"}

            else:

                return {}

    # 获取doi
    def getDoi(self, html):
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
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


if __name__ == '__main__':
    main = zhiwangPeriodocalService()
    # main.run()