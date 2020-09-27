# -*-coding:utf-8-*-

import sys
import os
import ast
import re
import time
from urllib.parse import quote,unquote
import requests
import hashlib
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
from lxml import etree
from lxml.html import fromstring, tostring
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")


class DomResultHolder:
    def __init__(self):
        self.dict = {}

    def get(self, type: object, text: object) -> object:
        if type in self.dict:
            return self.dict[type]
        if type == 'Selector':
            self.dict[type] = Selector(text=text)
            return self.dict[type]
        if type == 'BeautifulSoup':
            self.dict[type] = BeautifulSoup(text, 'html.parser')
            return self.dict[type]
        raise NotImplementedError

    def clear(self):
        self.dict.clear()


class Server(object):
    def __init__(self, logging):
        self.logging = logging
        self.dom_holder = DomResultHolder()

    def get_new_text(self):
        self.dom_holder.clear()

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取期刊名录总页数
    def getJournalPages(self, text):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            a_list = selector.xpath("//h2[contains(text(),'学科分类')]/following-sibling::ul[1]/li/a")
            for a in a_list:
                a_dict = {}
                href = a.xpath("./@href").extract_first()
                para = ast.literal_eval(re.findall(r"showlist(\(.*\))", href)[0])
                # 请求第一页
                # a_dict['num'] = 0
                a_dict['url'] = 'http://www.nssd.org/journal/list.aspx?p=1&t=0&e={}&h={}'.format(quote(para[0]),
                                                                                                 quote(para[1]))
                a_dict['xuekefenlei'] = a.xpath("./text()").extract_first()
                return_data.append(a_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊详情种子及附加信息
    def getJournalList(self, text):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            href_list = selector.xpath("//td[@class='title']/a/@href").extract()
            for href in href_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + href
                data_dict['s_xuekeleibie'] = ""
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # 获取学科分类名称及种子
    def getCatalogList(self, text):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            a_list = selector.xpath("//h2[contains(text(),'学科分类')]/following-sibling::ul[1]/li/a")
            for a in a_list:
                a_dict = {}
                href = a.xpath("./@href").extract_first()
                para = ast.literal_eval(re.findall(r"showlist(\(.*\))", href)[0])
                # 请求第一页
                # a_dict['num'] = 0
                a_dict['url'] = 'http://www.nssd.org/journal/list.aspx?p=1&t=0&e={}&h={}'.format(quote(para[0]), quote(para[1]))
                a_dict['s_xuekefenlei'] = a.xpath("./text()").extract_first()
                return_data.append(a_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊列表页总页数
    def getTotalPage(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            span = selector.xpath("//span[@class='total']/text()").extract_first()
            total_page = re.findall(r"\d+/(\d+)", span)[0]

        except Exception:
            return 1

        return total_page

    # 获取期刊详情种子及附加信息
    def getQiKanDetailUrl(self, text, xuekeleibie):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            href_list = selector.xpath("//ul[@class='cover_list']/li/a[@class='name']/@href").extract()
            for href in href_list:
                data_dict = {}
                data_dict['s_xuekeleibie'] = xuekeleibie
                data_dict['url'] = 'http://www.nssd.org' + href
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # 获取期刊年列表
    def getYears(self, text, xuekeleibie, qikanUrl):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            a_list = selector.xpath("//div[@id='qkyearslist']/ul/li/a")
            for a in a_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + a.xpath("./@href").extract_first().strip()
                data_dict['year'] = a.xpath("./text()").extract_first().strip().replace('年', '')
                data_dict['xuekeleibie'] = xuekeleibie
                data_dict['qikanUrl'] = qikanUrl

                return_data.append(data_dict)
                # yield data_dict

        except Exception:
            return return_data

        return return_data

    # 获取期号列表
    def getIssues(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            a_list = selector.xpath("//div[@id='numlist']/ul/li/a")
            for a in a_list:
                data_dict = {}
                data_dict['url'] = 'http://www.nssd.org' + a.xpath("./@href").extract_first().strip()
                data_dict['issue'] = re.findall(r"年(.*)期", a.xpath("./text()").extract_first().strip())[0]

                yield data_dict

        except Exception:
            return

    # 获取期论文刊详情种子及附加信息
    def getLunWenDetailUrl(self, text, qikanUrl, xuekeleibie, year, issue):
        return_data = []
        selector = Selector(text=text)
        try:
            tr_list = selector.xpath("//table[@class='t_list']//tr[position()>1]")
            for tr in tr_list:
                data_dict = {}
                try:
                    data_dict['url'] = 'http://www.nssd.org' + tr.xpath("./td[1]/a/@href").extract_first().strip()
                except:
                    continue
                try:
                    data_dict['authors'] = re.sub(r"[;；]", "|", tr.xpath("./td[2]/text()").extract_first().strip())
                except:
                    data_dict['authors'] = ''
                try:
                    data_dict['pdfUrl'] = 'http://www.nssd.org' + tr.xpath("./td[3]/a/@href").extract_first().strip()
                except:
                    data_dict['pdfUrl'] = ''
                data_dict['id'] = re.findall(r"id=(.*)?&?", data_dict['url'])[0]
                data_dict['qikanUrl'] = qikanUrl
                data_dict['xuekeleibie'] = xuekeleibie
                data_dict['year'] = year
                data_dict['issue'] = issue
                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # ---------------------
    # data script
    # ---------------------

    # ====== 期刊实体
    # 是否包含中文（判断语种）
    def hasChinese(self, data):
        for ch in data:
            if '\u4e00' <= ch <= '\u9fa5':
                return True

        return False

    # 标题
    def getJournalTitle(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            title = selector.xpath("//h1/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 英文标题
    def getParallelTitle(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            title = selector.xpath("//h1/following-sibling::em[1]/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 封面图片
    def getCover(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            src = selector.xpath("//div[@class='cover']/img/@src").extract_first().strip()
            if src.startswith('http'):
                imgUrl = src
            else:
                imgUrl = 'http://image.nssd.org' + src

        except Exception:
            imgUrl = ""

        return imgUrl

    # 简介
    def getAbstract(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            if selector.xpath("//p[strong[contains(text(), '简　　介')]]/span[@name='all']"):
                abstract = selector.xpath("//p[strong[contains(text(), '简　　介')]]/span[@name='all']/text()").extract_first().strip()
            else:
                abstract = selector.xpath("//p[strong[contains(text(), '简　　介')]]/text()").extract_first().strip()

        except Exception:
            abstract = ""

        return abstract

    # 主管单位/社长
    def getOneValue(self, text, para):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            value = selector.xpath("//p[strong[contains(text(), '{}')]]/text()".format(para)).extract_first().strip()

        except Exception:
            value = ""

        return value

    # 主办单位
    def getMoreValues(self, text, para):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            values = re.sub(r"[;；]", "|", selector.xpath("//p[strong[contains(text(), '{}')]]/text()".format(para)).extract_first().strip())

        except Exception:
            values = ""

        return values

    # 期刊变更
    def getHistory(self, text, para):
        soup = self.dom_holder.get(type='BeautifulSoup', text=text)
        # selector = Selector(text=text)
        try:
            value = soup.select("p:contains({})".format(para))[0].get_text()
            # value = selector.xpath("//p[strong[contains(text(), '{}')]]".format(para)).extract()
            history = ''.join(value).replace('期刊变更：', '')

        except Exception:
            history = ""

        return history

    # 电话
    def getTelephone(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            telephone = re.sub(r"\s+", "|", selector.xpath("//p[strong[contains(text(), '电　　话')]]/text()").extract_first().strip())

        except Exception:
            telephone = ""

        return telephone

    # 电子邮件/期刊网址
    def getHref(self, text, para):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            href = selector.xpath("//p[strong[contains(text(), '{}')]]/a/@href".format(para)).extract_first().strip()

        except Exception:
            href = ""

        return href

    # 期刊荣誉
    def getHonors(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            honors_list = selector.xpath("//div[@class='coreinfo']/text()").extract()
            honors = ''.join(honors_list).strip()

        except Exception:
            honors = ""

        return honors

    # 被收录数据库
    def getDatabases(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            li_list = selector.xpath("//div[@id='qkintro']/ul/li/text()").extract()
            databases = '|'.join(li_list)

        except Exception:
            databases = ""

        return databases

    # 学术评价url
    def getEvaluateUrl(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            href = selector.xpath("//span[@class='qkpj']/a/@href").extract_first().strip()
            if href.startswith('http'):
                evaluateUrl = href
            else:
                evaluateUrl = 'http://www.nssd.org' + href

        except Exception:
            evaluateUrl = ""

        return evaluateUrl

    # 学术评价
    def getEvaluate(self, text):
        return_data = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            tr_list = selector.xpath("//table[@class='t_list']//tr[position()>1]")
            for tr in tr_list:
                data_dict = {}
                # 年
                try:
                    year = tr.xpath("./td[1]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", year)
                    if pattern_value:
                        data_dict['year'] = year
                    else:
                        data_dict['year'] = ""
                except:
                    data_dict['year'] = ""
                # 发文量
                try:
                    published_volume = tr.xpath("./td[2]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", published_volume)
                    if pattern_value:
                        data_dict['published_volume'] = published_volume
                    else:
                        data_dict['published_volume'] = ""
                except:
                    data_dict['published_volume'] = ""
                # 被引次数
                try:
                    journal_cites = tr.xpath("./td[3]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", journal_cites)
                    if pattern_value:
                        data_dict['journal_cites'] = journal_cites
                    else:
                        data_dict['journal_cites'] = ""
                except:
                    data_dict['journal_cites'] = ""
                # 影响因子
                try:
                    influence_factor = tr.xpath("./td[4]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", influence_factor)
                    if pattern_value:
                        data_dict['influence_factor'] = influence_factor
                    else:
                        data_dict['influence_factor'] = ""
                except:
                    data_dict['influence_factor'] = ""
                # 立即指数
                try:
                    immediacy_index = tr.xpath("./td[5]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", immediacy_index)
                    if pattern_value:
                        data_dict['immediacy_index'] = immediacy_index
                    else:
                        data_dict['immediacy_index'] = ""
                except:
                    data_dict['immediacy_index'] = ""
                # 被引半衰期
                try:
                    cited_half_life = tr.xpath("./td[6]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", cited_half_life)
                    if pattern_value:
                        data_dict['cited_half_life'] = cited_half_life
                    else:
                        data_dict['cited_half_life'] = ""
                except:
                    data_dict['cited_half_life'] = ""
                # 引用半衰期
                try:
                    citing_half_life = tr.xpath("./td[7]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", citing_half_life)
                    if pattern_value:
                        data_dict['citing_half_life'] = citing_half_life
                    else:
                        data_dict['citing_half_life'] = ""
                except:
                    data_dict['citing_half_life'] = ""
                # 期刊他引率
                try:
                    cited_rate = tr.xpath("./td[8]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", cited_rate)
                    if pattern_value:
                        data_dict['cited_rate'] = cited_rate
                    else:
                        data_dict['cited_rate'] = ""
                except:
                    data_dict['cited_rate'] = ""
                # 平均引文率
                try:
                    mean_citing_rate = tr.xpath("./td[9]//text()").extract_first().strip()
                    pattern_value = re.search(r"\d+", mean_citing_rate)
                    if pattern_value:
                        data_dict['mean_citing_rate'] = mean_citing_rate
                    else:
                        data_dict['mean_citing_rate'] = ""
                except:
                    data_dict['mean_citing_rate'] = ""

                return_data.append(data_dict)

        except Exception:
            return return_data

        return return_data

    # 关联期刊
    def rela_journal(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '期刊'
        except Exception:
            return e

        return e

    # ====== 论文实体
    # 标题
    def getPaperTitle(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            title = selector.xpath("//h1/span/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 摘要
    def getPaperAbstract(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            abstract = selector.xpath("//p[@id='allAbstrack']/text()").extract_first().strip()

        except Exception:
            abstract = ""

        return abstract

    # 作者单位
    def getAuthorAffiliation(self, text):
        unit_list = []
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            affiliation_list = selector.xpath("//p[strong[contains(text(), '作者单位')]]/a/text()").extract()
            for unit in affiliation_list:
                uni = re.sub(r"\[\d+\]", "", unit)
                unit_list.append(uni)

            affiliation = '|'.join(unit_list).strip().strip(',')

        except Exception:
            affiliation = ""

        return affiliation

    # 期刊名称
    def getJournalName(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            name = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/a[1]/text()").extract_first().strip()

        except Exception:
            name = ""

        return name

    # 起始页
    def getStartPage(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            start_page = re.findall(r"期(.*?)-", ''.join(journal).strip())[0]

        except Exception:
            start_page = ""

        return start_page

    # 结束页
    def getEndPage(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            end_page = re.findall(r"-(.*?)[,，]?共", ''.join(journal).strip())[0]

        except Exception:
            end_page = ""

        return end_page

    # 总页数
    def getTotalPages(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            total_page = re.findall(r"共(\d+)页", ''.join(journal).strip())[0]

        except Exception:
            total_page = ""

        return total_page

    # 关键词/分类号
    def getFieldValues(self, text, para):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            values = selector.xpath("//p[strong[contains(text(), '{}')]]/a/text()".format(para)).extract()
            value = '|'.join(values)

        except Exception:
            value = ""

        return value

    # 项目基金
    def getFunders(self, text):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            funders = selector.xpath("//p[strong[contains(text(), '基金项目')]]/text()").extract()
            funder = re.sub(r"[;；]", "|", ''.join(funders).strip())

        except Exception:
            funder = ""

        return funder

    # 次数
    def getCount(self, text, para):
        selector = self.dom_holder.get(type='Selector', text=text)
        try:
            count = selector.xpath("//strong[contains(text(), '{}')]/following-sibling::span[1]/text()".format(para)).extract_first().strip()

        except Exception:
            count = ""

        return count

    # =========== 文档实体 =============
    # 获取文档
    def getDocs(self, pdfData, size):
        labelObj = {}
        return_docs = []
        try:
            if pdfData:
                if pdfData['url']:
                    picObj = {
                        'url': pdfData['url'],
                        'title': pdfData['bizTitle'],
                        'desc': "",
                        'sha': hashlib.sha1(pdfData['url'].encode('utf-8')).hexdigest(),
                        'format': 'PDF',
                        'size': size,
                        'ss': 'document'
                    }
                    return_docs.append(picObj)
                labelObj['全部'] = return_docs
        except Exception:
            labelObj['全部'] = []

        return labelObj

    # 关联文档
    def rela_document(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # 关联论文
    def rela_paper(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e


























