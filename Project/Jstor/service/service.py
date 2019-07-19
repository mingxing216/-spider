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



class QiKanLunWen_LunWenServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取各学科列表url
    def getSubjectUrlList(self, resp, index_url):
        return_list = []
        selector = Selector(text=resp)
        # 获取所有学科url所在的input标签
        url_list = selector.xpath("//fieldset[@id='disc']/ul/li/input")
        # 获取所有学科名称所在的label标签
        name_list = selector.xpath("//fieldset[@id='disc']/ul/li/label")
        # 遍历所有学科标签，获取每个学科中的name-value属性值,并拼成新的列表url,以及获取学科名称
        for i in range(len(url_list)):
            name = url_list[i].xpath("./@name").extract_first()
            value = url_list[i].xpath("./@value").extract_first()
            subject = re.sub(r'\s*\(.*\)', '', name_list[i].xpath("./span/text()").extract_first())
            url = index_url + '&' + name + '=' + value
            return_list.append({'url':url, 'xueKeLeiBie':subject})

        return return_list

    # 获取详情url
    def getDetailUrl(self, resp, xueke):
        return_list = []
        selector = Selector(text=resp)
        # 获取一页所有详情url
        url_list = selector.xpath("//div[@class='title']/h3/a/@href").extract()
        # 遍历每个详情url，加上域名，拼接成完整的url
        for url in url_list:
            url = 'https://www.jstor.org' + url
            return_list.append({'url':url, 'xueKeLeiBie':xueke})

        return return_list

    # 是否有下一页
    def hasNextPage(self, resp):
        selector = Selector(text=resp)
        try:
            next_page = 'https://www.jstor.org' + selector.xpath("//form[@id='searchFormTools']/div/ul/li/a[@id='next-page']/@href").extract_first()
        except:
            next_page = None

        return next_page

    # ================================= 获取字段值(模板1)

    # 获取script标签中的内容
    def getScript(self, resp):
        selector = Selector(text=resp)
        try:
            script_text = selector.xpath("//script[contains(text(),'contentData')]/text()").extract_first().strip()
            script = '{' + re.sub(r";$", "", re.sub(r"\s*utilsData\s*=\s*", "\"utilsData\":", re.sub(r"\s*userData\s*=\s*", "\"userData\":", re.sub(r"\s*reviveData\s*=\s*", "\"reviveData\":", re.sub(r"\s*parentContentData\s*=\s*", "\"parentContentData\":", re.sub(r"\s*searchData\s*=\s*", "\"searchData\":", re.sub(r"\s*contentData\s*=\s*", "\"contentData\":", re.sub(r"var\s+authorizationData\s*=\s*", "\"authorizationData\":", script_text)))))))) + '}'
            script_dict = json.loads(script)
            # print(json.dumps(script_dict, indent=4))
            # with open('script.txt', 'w')as f:
            #     f.write(scri)
            # print(script_list[0]['creativeCommons'])
        except Exception:
            script_dict = {}

        return script_dict

    # 获取字段
    def getField(self, script, para):
        text_dict = script
        try:
            if text_dict:
                fieldValue = str(text_dict['contentData'][para]).strip()
            else:
                fieldValue = ""
        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取多值字段
    def getMoreField(self, script, para):
        text_dict = script
        try:
            if text_dict:
                moreDataList = text_dict['contentData'][para]
                if isinstance(moreDataList, list):
                    moreData = "|".join(moreDataList)
                elif isinstance(moreDataList, str):
                    moreData = moreDataList.strip()
                else:
                    moreData = ""
            else:
                moreData = ""
        except Exception:
            moreData = ""

        return moreData

    # 获取卷期
    def getJuanQi(self, script):
        text_dict = script
        try:
            if text_dict:
                juanQi = text_dict['contentData']['volume'].strip() + ', ' + text_dict['contentData']['issue'].strip()
            else:
                juanQi = ""
        except Exception:
            juanQi = ""

        return juanQi

    # 获取出版商
    def getChuBanShang(self, script):
        text_dict = script
        try:
            if text_dict:
                chuBanShang = str(text_dict['contentData']['primaryPublisher']['publisherName']).strip()
            else:
                chuBanShang = ""
        except Exception:
            chuBanShang = ""

        return chuBanShang

    # 获取摘要
    def getZhaiYao(self, script):
        text_dict = script
        try:
            if text_dict:
                zhaiYao = re.findall(r"Abstract</h4>([\s\S]*</div>)</article>", str(text_dict['contentData']['infoTabRendition']))[0].replace("\n", "")
            else:
                zhaiYao = ""
        except Exception:
            zhaiYao = ""

        return zhaiYao

    # 关联组图
    def guanLianPics(self, url):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '组图'
        except Exception:
            return e

        return e

    # 关联论文
    def guanLianLunWen(self, url):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '论文'
        except Exception:
            return e

        return e

    # 获取组图
    def getPicUrl(self, script):
        return_pics = []
        text_dict = script
        try:
            if text_dict:
                pics = text_dict['contentData']['pageImages']
                shortDOI = text_dict['contentData']['shortDOI']
                if pics:
                    for pic in pics:
                        return_pics.append('https://www.jstor.org/stable/get_image/' + shortDOI + '?path=' + pic)
        except Exception:
            return return_pics

        return return_pics

    # 获取组图
    def getPics(self, script, title):
        labelObj = {}
        return_pics = []
        text_dict = script
        try:
            if text_dict:
                pics = text_dict['contentData']['pageImages']
                shortDOI = text_dict['contentData']['shortDOI']
                if pics:
                    for pic in pics:
                        picObj = {
                            'url': 'https://www.jstor.org/stable/get_image/' + shortDOI + '?path=' + pic,
                            'title': title,
                            'desc': ""
                        }
                        return_pics.append(picObj)
                labelObj['全部'] = return_pics
        except Exception:
            labelObj['全部'] = []

        return labelObj


    # 获取参考文献
    def getCanKaoWenXian(self, script):
        data_list = []
        text_dict = script
        try:
            if text_dict:
                first_list = text_dict['contentData']['references']['reference_blocks'][0]['reference_content']
                # print(json.dumps(first_list, indent=4))
                if first_list:
                    for first in first_list:
                        label = first['label']
                        if not label:
                            second_dict = first['reference_data'][0]
                            # print(json.dumps(second_dict, indent=4))
                            data_dict = {}
                            if second_dict:
                                data = second_dict['text']

                                if 'http' in data:
                                    try:
                                        data_dict['内容'] = re.findall(r"(.*)\s*http", data)[0]
                                    except Exception:
                                        data_dict['内容'] = ""
                                    try:
                                        data_dict['doi'] = re.findall(r"https://doi.org/(.*)", data)[0]
                                    except Exception:
                                        data_dict['doi'] = ""
                                else:
                                    try:
                                        data_dict['内容'] = data
                                    except Exception:
                                        data_dict['内容'] = ""

                                    data_dict['doi'] = ""

                                # try:
                                #     data_dict['作者'] = re.findall(r"(.*?)\s*[\(\（]*\d+", data)[0]
                                # except Exception:
                                #     data_dict['作者'] = ""
                                # try:
                                #     data_dict['日期'] = re.findall(r"\.\s*[\(\（]*([\d-]+?)[\)\）]*\.", data)[0]
                                # except Exception:
                                #     data_dict['日期'] = ""
                                # try:
                                #     if not data_dict['作者']:
                                #         data_dict['标题'] = data
                                #     else:
                                #         if 'http' in data:
                                #             data_dict['标题'] = re.findall(r"\d+[\)\）]*\.\s*(.*?)\.\s*http", data)[0]
                                #         else:
                                #             data_dict['标题'] = re.findall(r"\d+[\)\）]*\.\s*(.*)", data)[0]
                                # except Exception:
                                #     data_dict['标题'] = ""
                                # try:
                                #     data_dict['doi'] = re.findall(r"https://doi.org/(.*)", data)[0]
                                # except Exception:
                                #     data_dict['doi'] = ""

                                data_list.append(data_dict)

        except:
            return data_list

        return data_list

    # 获取关联期刊
    def getGuanLianQiKan(self, script):
        text_dict = script
        # 创建关联对象
        e = {}
        try:
            if text_dict:
                e['url'] = 'https://www.jstor.org' + str(text_dict['contentData']['publicationUrl']).strip()
                e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
                e['ss'] = '期刊'
        except Exception:
            return e

        return e

    # 获取关联文档
    def getGuanLianWenDang(self, script):
        text_dict = script
        # 创建关联对象
        e = {}
        try:
            if text_dict:
                e['url'] = 'https://www.jstor.org/stable/pdf/' + str(text_dict['contentData']['shortDOI']).strip() + '.pdf'
                e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
                e['ss'] = '文档'
        except Exception:
            return e

        return e

    # ===============================获取字段值(模板2)

    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1[contains(@class, 'title')]//text()").extract()
            title = ''.join(tit).strip()

        except Exception:
            title = ""

        return title

    # 获取作者
    def getZuoZhe(self, select):
        selector = select
        try:
            zuozhe_data = selector.xpath("//div[@class='contrib']/text()").extract_first().strip()
            zuozhe = re.sub(r"\s*[,，]\s*", "|", re.sub(r"\s*and\s*", "|", re.sub(r".*[:：]", "", zuozhe_data).strip()))

        except Exception:
            zuozhe = ""

        return zuozhe

    # 获取期刊名称
    def getIssn(self, select):
        selector = select
        try:
            issn = selector.xpath("//div[contains(@class, 'issn')]/text()").extract_first().strip()

        except Exception:
            issn = ""

        return issn

    # 获取巻期
    def getJuanQis(self, select):
        selector = select
        try:
            juan = selector.xpath("//div[contains(@class, 'break-word')]/text()").extract_first().strip()
            juanqi = re.findall(r"(Vol.*No\.\s*\d+)", juan)[0]

        except Exception:
            juanqi = ""

        return juanqi

    # 获取所在页码
    def getSuoZaiYeMa(self, select):
        selector = select
        try:
            juan = selector.xpath("//div[contains(@class, 'break-word')]/text()").extract_first().strip()
            suozaiyema = re.findall(r"[,，]\s*(pp\.\s*[\d-]*)", juan)[0]

        except Exception:
            suozaiyema = ""

        return suozaiyema

    # 获取页数
    def getYeShu(self, select):
        selector = select
        try:
            count = selector.xpath("//div[@class='count']/text()").extract_first().strip()
            yeshu = re.findall(r"[:：]\s*(.*)", count)[0]

        except Exception:
            yeshu = ""

        return yeshu

    # 获取出版商
    def getChuBanShangs(self, select):
        selector = select
        try:
            chu = selector.xpath("//div[@class='publisher']//text()").extract()
            chuban = ''.join(chu).strip()
            chubanshang = re.findall(r"[:：]\s*(.*)", chuban)[0]

        except Exception:
            chubanshang = ""

        return chubanshang

    # 获取摘要
    def getZhaiYaos(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//div[contains(@class, 'journal_description')]")[0]
            zhaiyao = re.sub(r"\n", "", re.sub(r"<strong>.*</strong>", "", tostring(result).decode('utf-8'))).strip()

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取关键词
    def getGuanJianCi(self, select):
        selector = select
        try:
            guanjian = selector.xpath("//div[contains(@class, 'topics-list')]/a/text()").extract()
            guanjianci = '|'.join(guanjian).strip()

        except Exception:
            guanjianci = ""

        return guanjianci

    # 获取关联期刊
    def getGuanLianQiKans(self, select):
        selector = select
        # 创建关联对象
        e = {}
        try:
            e['url'] = 'https://www.jstor.org'+ selector.xpath("//li[contains(@class, 'breadcrumb-issue')]/a/@href").extract_first()
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '期刊'
        except Exception:
            return e

        return e

class QiKanLunWen_QiKanServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取选择器
    def getSelector(self, resp):
        selector = Selector(text=resp)

        return selector

    # 获取标题
    def getTitle(self, select):
        selector = select
        try:
            tit = selector.xpath("//h1[contains(@class, 'journal-name')]//text()").extract()
            title = ''.join(tit).strip()

        except Exception:
            title = ""

        return title

    # 获取摘要
    def getZhaiYao(self, html):
        tree = etree.HTML(html)
        try:
            result = tree.xpath("//div[contains(@class, 'journal_description')]")[0]
            zhaiyao = re.sub(r"\n", "", re.sub(r"<strong>.*</strong>", "", tostring(result).decode('utf-8'))).strip()

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取覆盖范围
    def getFuGaiFanWei(self, select):
        selector = select
        try:
            fugaifanwei = selector.xpath("//div[@id='journal_info_drop']/div[contains(@class, 'coverage-period')]/text()").extract_first().strip()

        except Exception:
            fugaifanwei = ""

        return fugaifanwei

    # 获取国际标刊号
    def getIssn(self, select):
        selector = select
        try:
            issn = selector.xpath("//div[@class='issn mtm']/text()").extract_first().strip()

        except Exception:
            issn = ""

        return issn

    # 获取EISSN
    def getEissn(self, select):
        selector = select
        try:
            eissn = selector.xpath("//div[@class='eissn mtm']/text()").extract_first().strip()

        except Exception:
            eissn = ""

        return eissn

    # 获取学科类别
    def getXueKeLeiBie(self, select):
        selector = select
        try:
            xueke = selector.xpath("//div[contains(@class, 'subjects')]/text()").extract_first().strip()
            xuekeleibie = re.sub(r"\n", "", xueke)

        except Exception:
            xuekeleibie = ""

        return xuekeleibie

    # 获取出版社
    def getChuBanShe(self, select):
        selector = select
        try:
            chu = selector.xpath("//div[@class='publisher']//text()").extract()
            chuban = ''.join(chu).strip()
            chubanshe = re.findall(r"[:：]\s*(.*)", chuban)[0]

        except Exception:
            chubanshe = ""

        return chubanshe