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

    # 获取第一分类列表
    def getIndexClassList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        try:
            label_list = selector.xpath("//div[@class='leftlist_1']/span/img[contains(@id, 'first')]/@onclick").extract()

            for label in label_list:
                lower_url = "https://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
                try:
                    lower_data = ast.literal_eval(re.findall("(\(.*\))", label)[0])
                    return_data.append(lower_url.format(lower_data[0], lower_data[2]))
                except:
                    continue

        except Exception:
            return return_data

        return return_data

    # 获取第二分类列表
    def getSecondClassList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        try:
            dd_list = selector.xpath("//dd/span/img[contains(@id, 'first')]/@onclick").extract()

            for dd in dd_list:
                lower_url = "https://kns.cnki.net/kns/request/NaviGroup.aspx?code={}&tpinavigroup={}"
                try:
                    lower_data = ast.literal_eval(re.findall("(\(.*\))", dd)[0])
                    return_data.append(lower_url.format(lower_data[0], lower_data[2]))
                except:
                    continue

        except Exception:
            return return_data

        return return_data

    # 获取第三分类号
    def getCategoryNumber(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            dd_list = selector.xpath("//dd/span/input[@id='selectbox']/@value").extract()

            for category in dd_list:
                return_data.append(category)

        except Exception:
            return return_data

        return return_data

    # 获取年列表
    def getYearList(self, resp):
        if re.findall(r"<a>(\d+)</a>", resp):
            return re.findall(r"<a>(\d+)</a>", resp)

        else:
            return []

    # # 获取年列表页参数
    # def getYearParas(self, resp):
    #     para_list = []
    #     selector = Selector(text=resp)
    #     try:
    #         tags = selector.xpath("//input")
    #         for tag in tags:
    #             para_id = tag.xpath("./@id").extract_first()
    #             para_value = tag.xpath("./@value").extract_first()
    #             para_list.append([para_id, para_value])
    #
    #     except Exception:
    #         return para_list
    #
    #     return para_list


    # 获取详情种子
    def getDetailUrl(self, resp):
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

                url = ('https://dbpub.cnki.net/grid2008/dbpub/detail.aspx?'
                       'dbcode={}&'
                       'dbname={}&'
                       'filename={}').format(dbcode, dbname, filename)

                return_data.append({'url': url})
            except:
                continue

        return return_data

    # 获取下一页url
    def hasNextUrl(self, resp):
        selector = Selector(text=resp)
        try:
            href = selector.xpath("//div[@class='TitleLeftCell']/a[text()='下一页']/@href").extract_first()
            if not href:
                return None
            else:
                next_page = 'https://kns.cnki.net/kns/brief/brief.aspx' + str(href)
                return next_page
        except Exception:
            return None


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



























