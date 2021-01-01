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
from langid import langid
from pyquery import PyQuery as pq
from lxml import etree
from lxml.html import fromstring, tostring
from scrapy import Selector

from Utils import timer
from Utils.captcha import RecognizeCode

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))


class DomResultHolder(object):
    def __init__(self):
        self.dict = {}

    def get(self, mode, text):
        if mode in self.dict:
            return self.dict[mode]

        if mode == 'Selector':
            self.dict[mode] = Selector(text=text)
            return self.dict[mode]

        if mode == 'BeautifulSoup':
            self.dict[mode] = BeautifulSoup(text, 'html.parser')
            return self.dict[mode]

        raise NotImplementedError

    def clear(self):
        self.dict.clear()


class Server(object):
    def __init__(self, logging):
        self.logger = logging
        self.dom_holder = DomResultHolder()

    def clear(self):
        self.dom_holder.clear()

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    @staticmethod
    def get_eval_response(task_data):
        return ast.literal_eval(task_data)

    # 获取期刊列表页总页数
    def get_journal_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            span = selector.xpath("//span[@id='lblCurrentPage']/text()").extract_first()
            total_page = re.findall(r"\d+/(\d+)", span)[0]

        except Exception:
            self.clear()
            return 1

        self.clear()
        return total_page

    # 获取期刊详情种子及附加信息
    def get_journal_list(self, text):
        journal_data_list = []
        paper_catalog_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            div_list = selector.xpath("//div[a[@class='btnnoimg']]")
            for a in div_list:
                journal_dict = {}
                paper_dict = {}
                journal_dict['url'] = 'http://103.247.176.188/' + a.xpath("./a[@class='btnnoimg']/@href").extract_first()
                journal_data_list.append(journal_dict)

                paper_dict['url'] = 'http://103.247.176.188/' + a.xpath("./a[@class='btnnoimg2']/@href").extract_first() + '&ob=dd'
                paper_dict['journalUrl'] = journal_dict['url']
                paper_catalog_list.append(paper_dict)

        except Exception:
            self.clear()
            return journal_data_list, paper_catalog_list

        self.clear()
        return journal_data_list, paper_catalog_list

    # 获取论文列表页总页数
    def get_paper_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            total_page = selector.xpath("//div[@class='term-title']//td/b/text()").extract_first()

        except Exception:
            self.clear()
            return 1

        self.clear()
        return total_page

    # 获取论文详情及全文种子
    def get_paper_list(self, text, journal_url):
        paper_data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            div_list = selector.xpath("//div[a[@class='btnnoimg']]")
            for a in div_list:
                paper_dict = {}
                if a.xpath("./a[@class='btnnoimg']"):
                    paper_dict['url'] = 'http://103.247.176.188/' + a.xpath("./a[@class='btnnoimg']/@href").extract_first()
                else:
                    continue
                if a.xpath("./a[@class='btnnoimg2']"):
                    paper_dict['pdfUrl'] = 'http://103.247.176.188/' + a.xpath("./a[@class='btnnoimg2']/@href").extract_first()
                else:
                    paper_dict['pdfUrl'] = ''
                paper_dict['journalUrl'] = journal_url
                paper_data_list.append(paper_dict)

        except Exception:
            self.clear()
            return paper_data_list

        self.clear()
        return paper_data_list

    # 获取下一页
    def get_next_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            next_a = selector.xpath("//div[contains(@class, 'pages')]/a[text()='下一页']/@href").extract_first()
            next_url = 'http://103.247.176.188/' + next_a

        except Exception:
            self.clear()
            next_url = None

        self.clear()
        return next_url

    # 获取验证码参数
    def get_captcha(self, text):
        captcha_data = {}
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            captcha_data['__VIEWSTATE'] = selector.xpath("//input[@id='__VIEWSTATE']/@value").extract_first()
            captcha_data['__EVENTVALIDATION'] = selector.xpath("//*[@id='__EVENTVALIDATION']/@value").extract_first()
            captcha_data['btnOk'] = selector.xpath("//*[@id='btnOk']/@value").extract_first()

        except Exception:
            self.clear()
            return captcha_data

        self.clear()
        return captcha_data

    # 获取图片url
    def get_img_url(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            img_url = 'http://103.247.176.188/' + selector.xpath("//img[@id='imgCode1']/@src").extract_first()

        except Exception:
            self.clear()
            return ''

        self.clear()
        return img_url

    # 获取学科分类名称及种子
    def getCatalogList(self, text):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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



    # 获取期刊详情种子及附加信息
    def getQiKanDetailUrl(self, text, xuekeleibie):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            a_list = selector.xpath("//div[@id='numlist']/ul/li/a")
            for a in a_list:
                data_dict = {'url': 'http://www.nssd.org' + a.xpath("./@href").extract_first().strip(),
                             'issue': re.findall(r"年(.*)期", a.xpath("./text()").extract_first().strip())[0]}

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

    # 语种识别
    def get_lang(self, text):
        return langid.classify(text)[0]

    # 标题
    def get_journal_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h1/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 英文标题
    def getParallelTitle(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h1/following-sibling::em[1]/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 封面图片
    def getCover(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            src = selector.xpath("//div[@class='cover']/img/@src").extract_first().strip()
            if src.startswith('http'):
                imgUrl = src
            else:
                imgUrl = 'http://image.nssd.org' + src

        except Exception:
            imgUrl = ""

        return imgUrl

    # 字段值通用获取
    def get_normal_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(para)).extract_first().strip()

        except Exception:
            field_value = ""

        return field_value

    # 字段多值获取
    def get_multi_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(para)).extract_first().strip()
            multi_avlue = re.sub(r"\s*[,，]\s*", "|", field_value)

        except Exception:
            multi_avlue = ""

        return multi_avlue

    # 中图分类
    def get_classification_value(self, text, para):
        classi_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(para)).extract_first().strip()
            value_list = re.split(r"[,，]", field_value)
            for value in value_list:
                classi_dict = {
                    'code': re.split(r"[:：]", value)[0].strip(),
                    'type': re.split(r"[:：]", value)[1].strip()
                }
                classi_list.append(classi_dict)

        except Exception:
            return classi_list

        return classi_list

    # 期刊网址
    def get_journal_website(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            website = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/a/@href".format(para)).extract_first().strip()

        except Exception:
            website = ""

        return website

    # 简介
    def get_abstract(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            value = selector.xpath("//p[strong[contains(text(), '{}')]]/text()".format(para)).extract_first().strip()

        except Exception:
            value = ""

        return value

    # 主办单位
    def getMoreValues(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            values = re.sub(r"[;；]", "|", selector.xpath("//p[strong[contains(text(), '{}')]]/text()".format(para)).extract_first().strip())

        except Exception:
            values = ""

        return values

    # 期刊变更
    def getHistory(self, text, para):
        soup = self.dom_holder.get(mode='BeautifulSoup', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            telephone = re.sub(r"\s+", "|", selector.xpath("//p[strong[contains(text(), '电　　话')]]/text()").extract_first().strip())

        except Exception:
            telephone = ""

        return telephone

    # 电子邮件/期刊网址
    def getHref(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            href = selector.xpath("//p[strong[contains(text(), '{}')]]/a/@href".format(para)).extract_first().strip()

        except Exception:
            href = ""

        return href

    # 期刊荣誉
    def getHonors(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            honors_list = selector.xpath("//div[@class='coreinfo']/text()").extract()
            honors = ''.join(honors_list).strip()

        except Exception:
            honors = ""

        return honors

    # 被收录数据库
    def getDatabases(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            li_list = selector.xpath("//div[@id='qkintro']/ul/li/text()").extract()
            databases = '|'.join(li_list)

        except Exception:
            databases = ""

        return databases

    # 学术评价url
    def getEvaluateUrl(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h1/span/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 摘要
    def getPaperAbstract(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            abstract = selector.xpath("//p[@id='allAbstrack']/text()").extract_first().strip()

        except Exception:
            abstract = ""

        return abstract

    # 作者单位
    def getAuthorAffiliation(self, text):
        unit_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            name = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/a[1]/text()").extract_first().strip()

        except Exception:
            name = ""

        return name

    # 起始页
    def getStartPage(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            start_page = re.findall(r"期(.*?)-", ''.join(journal).strip())[0]

        except Exception:
            start_page = ""

        return start_page

    # 结束页
    def getEndPage(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            end_page = re.findall(r"-(.*?)[,，]?共", ''.join(journal).strip())[0]

        except Exception:
            end_page = ""

        return end_page

    # 总页数
    def getTotalPages(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            journal = selector.xpath("//p[strong[contains(text(), '期　　刊')]]/text()").extract()
            total_page = re.findall(r"共(\d+)页", ''.join(journal).strip())[0]

        except Exception:
            total_page = ""

        return total_page

    # 关键词/分类号
    def getFieldValues(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            values = selector.xpath("//p[strong[contains(text(), '{}')]]/a/text()".format(para)).extract()
            value = '|'.join(values)

        except Exception:
            value = ""

        return value

    # 项目基金
    def getFunders(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            funders = selector.xpath("//p[strong[contains(text(), '基金项目')]]/text()").extract()
            funder = re.sub(r"[;；]", "|", ''.join(funders).strip())

        except Exception:
            funder = ""

        return funder

    # 次数
    def getCount(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
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


class CaptchaProcessor(object):
    def __init__(self, server, downloader, session, logger):
        self.server = server
        self.downloader = downloader
        self.session = session
        self.logger = logger
        self.recognize_code = RecognizeCode(self.logger)
        self.captcha_timer = timer.Timer()
        self.total_timer = timer.Timer()
        self.request_timer = timer.Timer()

    def is_captcha_page(self, resp):
        if len(resp.content) > 2048:
            return False
        if '验证码' in resp.text:
            return True
        return False

    def process_first_request(self, url, method, s):
        self.logger.info('process start | 请求开始 | url: {}'.format(url))
        self.total_timer.start()
        self.request_timer.start()
        resp = self.downloader.get_resp(url=url, method=method, s=s)
        self.logger.info('process | 一次请求完成时间 | use time: {} | url: {}'.format(self.request_timer.use_time(), resp.url))
        return resp

    def process(self, resp):
        retry_count = 5
        captcha_page = self.is_captcha_page(resp)
        for i in range(retry_count):
            if captcha_page:
                self.captcha_timer.start()
                # 获取验证码及相关参数
                form_data = self.server.get_captcha(resp.text)
                image_url = self.server.get_img_url(resp.text)
                img_content = self.downloader.get_resp(url=image_url, method='GET', s=self.session).content
                code = self.recognize_code.image_data(img_content, show=False, length=4, invalid_charset="^0-9^A-Z^a-z")
                form_data['iCode'] = code
                self.logger.info('process | 一次验证码处理完成 | use time: {}'.format(self.captcha_timer.use_time()))
                # 带验证码访问
                self.request_timer.start()
                real_url = resp.url
                resp = self.downloader.get_resp(url=real_url, method='POST', data=form_data, s=self.session)
                captcha_page = self.is_captcha_page(resp)
                self.recognize_code.report(img_content, code, not captcha_page)
                self.logger.info('process | 一次请求完成时间 | use time: {} | url: {}'.format(self.request_timer.use_time(), resp.url))
            else:
                self.logger.info('process end | 请求成功总时间 | use time: {} | url: {} | count: {}'.format(self.total_timer.use_time(), resp.url, i))
                return resp

        self.logger.error('process end | 验证码识别失败总时间 | use time: {} | url: {} | count: {}'.format(self.total_timer.use_time(), resp.url, retry_count))

        return
