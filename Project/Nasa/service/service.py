# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import ast
import json
import hashlib
from scrapy.selector import Selector
from lxml import etree
from lxml.html import fromstring, tostring

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class LunWen_LunWenServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取script标签中的内容
    def getScript(self, resp):
        selector = Selector(text=resp)
        try:
            script_text = selector.xpath("//script[contains(text(),'global.document.metadata')]/text()").extract_first().strip()
            script = re.sub(r";$", "", re.sub(r".*global\.document\.metadata=", "", re.sub(r"[\n\r\t]", "", script_text)))
            script_dict = json.loads(script)
            # print(json.dumps(script_dict, indent=4))
            # with open('script.txt', 'w')as f:
            #     f.write(script)
            # print(script_list[0]['creativeCommons'])
        except Exception:
            script_dict = {}

        return script_dict

    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取会议详情页，学科类别
    def getPaperPara(self, selector):
        papers = [{'name': 'Conference Paper', 'es': '会议文件'},
                  {'name': 'Conference Proceedings', 'es': '会议论文'},
                  {'name': 'Journal Article', 'es': '期刊论文'},
                  {'name': 'Masters Thesis', 'es': '硕士论文'},
                  {'name': 'PhD Dissertation', 'es': '博士论文'},
                  {'name': 'Thesis', 'es': '论文'}]
        try:
            labels = selector.xpath("//div[@id='divDocumentType']/div[@id='FakeScrollableList']/table/tr/td/label")
            for label in labels:
                content = label.xpath("./text()").extract_first().strip()
                for paper in papers:
                    if content == paper['name']:
                        num = re.findall(r"(\d+).*", label.xpath("./input/@value").extract_first())[0].strip()
                        paper['url'] = 'https://ntrs.nasa.gov/search.jsp?N=' + num

        except Exception:
            return None

        return papers

    # 获取会议论文详情页
    def getLunWenProfile(self, selector, es):
        return_list = []
        try:
            profile_url = selector.xpath("//table[@class='recordTable']/tr/td")
            for url in profile_url:
                profile_dict = {}
                profile_dict['lunwenUrl'] = 'https://ntrs.nasa.gov/' + url.xpath("./a/@href").extract_first().strip()
                try:
                    profile_dict['title'] = url.xpath("./a/text()").extract_first().strip()
                except Exception:
                    profile_dict['title'] = ''
                try:
                    profile_dict['pdfUrl'] = url.xpath("./div/a[contains(text(), 'View Document')]/@href").extract_first().strip()
                except Exception:
                    profile_dict['pdfUrl'] = ''
                try:
                    pdf = url.xpath("./div/a[contains(text(), 'View Document')]/../text()").extract()
                    pdfSize = re.sub(r"[\[PDF Size:\]]", "", re.sub(r"[\r\n\t]", "", ''.join(pdf))).strip()
                    profile_dict['pdfSize'] = pdfSize
                except Exception:
                    profile_dict['pdfSize'] = ''
                profile_dict['es'] = es

                return_list.append(profile_dict)

        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def nextPages(self, selector):
        try:
            nextPage = 'https://ntrs.nasa.gov/' + selector.xpath("//div[@id='paging'][last()]/div/a[contains(text(), 'Next')]/@href").extract_first().strip()

        except:
            nextPage = None

        return nextPage

    # ================================= 获取会议论文实体字段值
    # 获取标题
    def getTitle(self, selector):
        try:
            title = selector.xpath("//td[@id='recordtitle']/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 获取数字对象标识符
    def getDoi(self, selector):
        try:
            fieldValue = selector.xpath("//td[@id='colTitle' and contains(text(), 'External Online Source')]/following-sibling::td[1]/div/a[contains(text(), 'doi')]/text()").extract_first().replace('doi:', '').strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取字段
    def getField(self, selector, para):
        try:
            fieldValue = selector.xpath("//td[@id='colTitle' and contains(text(), '" + para + "')]/following-sibling::td[1]/text()").extract_first().strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取多值字段
    def getMoreField(self, selector, para):
        try:
            fieldValue = selector.xpath("//td[@id='colTitle' and contains(text(), '" + para + "')]/following-sibling::td[1]/text()").extract_first().replace(';', '|').strip()

        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取作者
    def getZuoZhe(self, selector):
        try:
            authors = selector.xpath("//td[@id='colTitle' and contains(text(), 'Author')]/following-sibling::td[1]//table/tr/td[1]/text()").extract()
            zuozhe = '|'.join(authors)

        except Exception:
            zuozhe = ""

        return zuozhe

    # 获取摘要
    def getZhaiYao(self, resp):
        tree = etree.HTML(resp)
        try:
            result = tree.xpath("//td[@id='colTitle' and contains(text(), 'Abstract')]/following-sibling::td[1]")[0]
            htmlValue = re.sub(r"[\n\r\t]", "", tostring(result).decode('utf-8')).strip()

        except Exception:
            htmlValue = ""

        return htmlValue

    # 获取关键词
    def getGuanJianCi(self, selector):
        try:
            try:
                terms = selector.xpath("//td[@id='colTitle' and contains(text(), 'NASA Terms')]/following-sibling::td[1]/text()").extract_first().strip().split(';')

            except Exception:
                terms = []
            try:
                others = selector.xpath("//td[@id='colTitle' and contains(text(), 'Other Descriptors')]/following-sibling::td[1]/text()").extract_first().strip().split(';')
            except Exception:
                others = []

            terms.extend(others)
            keywords = [x for x in terms if x != '']
            keyword = '|'.join(keywords)

        except Exception:
            keyword = ''

        return keyword

    # 关联作者
    def guanLianZuoZhe(self, selector, url):
        result = []
        try:
            authors = selector.xpath("//td[@id='colTitle' and contains(text(), 'Author')]/following-sibling::td[1]//table/tr")
            for author in authors:
                e = {}
                try:
                    name = author.xpath("./td[1]/text()").extract_first().strip()
                except Exception:
                    name = ""
                try:
                    danwei = author.xpath("./td[2]/span/text()").extract_first().strip()
                except Exception:
                    danwei = ""
                e['name'] = name
                e['url'] = url
                sha = e['url'] + '#' + e['name'] + '#' + danwei
                e['sha'] = hashlib.sha1(sha.encode('utf-8')).hexdigest()
                e['ss'] = '人物'
                result.append(e)
        except Exception:
            return result

        return result

    # 关联文档
    def guanLianWenDang(self, url):
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    #===============================获取作者实体字段值
    # 获取标题
    def getAuthorTitle(self, content):
        try:
            title = content.xpath("./td[1]/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 获取所在单位
    def getDanWei(self, content):
        try:
            title = content.xpath("./td[2]/span/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 获取ORCID
    def getORCID(self, content):
        try:
            orcid = re.sub(r".*orcid.org\/", "", content.xpath("./td[1]/a/@href").extract_first()).strip()

        except Exception:
            orcid = ""

        return orcid
