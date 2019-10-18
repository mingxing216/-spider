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



class HuiYiLunWen_LunWenServer(object):
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
    def getHuiYiProfile(self, json):
        return_list = []
        try:
            records = json['records']
            for record in records:
                try:
                    for huiyi in record['titleHistory']:
                        profile = {}
                        profile['number'] = huiyi['publicationNumber']
                        profile['url'] = 'https://ieeexplore.ieee.org' + huiyi['publicationLink']
                        return_list.append(profile)

                except Exception:
                    profile = {}
                    profile['number'] = record['publicationNumber']
                    profile['url'] = 'https://ieeexplore.ieee.org' + record['publicationLink']
                    return_list.append(profile)

        except Exception:
            return return_list

        return return_list

    # 获取会议论文列表页接口url，post参数，学科类别
    def getCatalogUrl(self, json, url):
        return_dict = {}
        try:
            xueke_list = []
            topics = json['pubTopics']
            for topic in topics:
                xueke_list.append(topic['name'])
            xueKeLeiBie = '|'.join(xueke_list)
        except Exception:
            xueKeLeiBie = ''

        try:
            return_dict['punumber'] = url['number']
            return_dict['isnumber'] = json['currentIssue']['issueNumber']
            return_dict['url'] = 'https://ieeexplore.ieee.org/rest/search/pub/' + str(return_dict['punumber']) + '/issue/' + str(return_dict['isnumber']) + '/toc'
            return_dict['parenUrl'] = url['url']
            return_dict['xueKeLeiBie'] = xueKeLeiBie

        except Exception:
            return return_dict

        return return_dict

    # 获取会议论文详情页
    def getLunWenProfile(self, json, huiyi, xueke):
        return_list = []
        try:
            records = json['records']
            for record in records:
                profile_dict = {}
                profile_dict['lunwenNumber'] = record['articleNumber']
                profile_dict['huiYiUrl'] = huiyi
                profile_dict['xueKeLeiBie'] = xueke
                try:
                    profile_dict['lunwenUrl'] = 'https://ieeexplore.ieee.org' + record['documentLink']
                except Exception:
                    profile_dict['lunwenUrl'] = 'https://ieeexplore.ieee.org/document/' + record['articleNumber']
                try:
                    profile_dict['title'] = record['articleTitle']
                except Exception:
                    profile_dict['title'] = ''
                try:
                    profile_dict['pdfUrl'] = 'https://ieeexplore.ieee.org' + record['pdfLink']
                except Exception:
                    profile_dict['pdfUrl'] = ''
                try:
                    profile_dict['daXiao'] = record['pdfSize']
                except Exception:
                    profile_dict['daXiao'] = ''
                return_list.append(profile_dict)

        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def totalPages(self, json):
        try:
            totalPage = json['totalPages']
            if totalPage > 1:
                totalPages = totalPage
            else:
                totalPages = None
        except:
            totalPages = None

        return totalPages

    # ================================= 获取会议论文实体字段值

    # 获取字段
    def getField(self, script, para):
        text_dict = script
        try:
            if text_dict:
                fieldValue = str(text_dict[para]).strip()
            else:
                fieldValue = ""
        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取ISBN、ISSN
    def getGuoJiField(self, script, para):
        text_dict = script
        try:
            return_dict = {}
            fields = text_dict[para]
            for field in fields:
                return_dict[field['format']] = field['value']

        except Exception:
            return_dict = ""

        return return_dict

    # 获取作者
    def getZuoZhe(self, script):
        try:
            author_list = []
            authors = script['authors']
            for author in authors:
                author_list.append(author['name'])
            zuozhe = '|'.join(author_list)

        except Exception:
            zuozhe = ''

        return zuozhe

    # 获取关键词
    def getGuanJianCi(self, script):
        try:
            keyword_list = []
            keywords = script['keywords']
            for keyword in keywords:
                keyword_list.extend(keyword['kwd'])
            guanjianci = '|'.join(keyword_list)

        except Exception:
            guanjianci = ''

        return guanjianci

    # 获取时间
    def getShiJian(self, script):
        try:
            return_dict = {}
            return_dict['Y'] = script['publicationYear']
        except Exception:
            return_dict = ""

        return return_dict

    # 获取页数
    def getYeShu(self, script):
        try:
            yeShu = script['startPage'] + ' - ' + script['endPage']

        except Exception:
            yeShu = ""

        return yeShu

    # 是否有参考/引证文献
    def hasWenXian(self, script, para):
        try:
            cankaowenxian = script['sections'][para]

        except Exception:
            cankaowenxian = ""

        return cankaowenxian

    # 参考文献
    def canKaoWenXian(self, content):
        return_list = []
        try:
            for reference in content['references']:
                return_dict = {}
                try:
                    return_dict['序号'] = reference['order']
                except Exception:
                    return_dict['序号'] = ""
                try:
                    return_dict['内容'] = reference['text']
                except Exception:
                    return_dict['内容'] = ""
                try:
                    return_dict['链接'] = 'https://ieeexplore.ieee.org' + reference['links']['documentLink']
                except Exception:
                    return_dict['链接'] = ""

                return_list.append(return_dict)

        except Exception:
            return return_list

        return return_list

    # 引证文献
    def yinZhengWenXian(self, content):
        return_list = []
        try:
            for citations in content['paperCitations'].values():
                for citation in citations:
                    return_dict = {}
                    try:
                        return_dict['序号'] = citation['order']
                    except Exception:
                        return_dict['序号'] = ""
                    try:
                        return_dict['内容'] = citation['displayText']
                    except Exception:
                        return_dict['内容'] = ""
                    try:
                        return_dict['链接'] = 'https://ieeexplore.ieee.org' + citation['links']['documentLink']
                    except Exception:
                        return_dict['链接'] = ""

                    return_list.append(return_dict)

        except Exception:
            return return_list

        return return_list

    # 关联作者
    def guanLianZuoZhe(self, script, url):
        result = []
        try:
            for author in script['authors']:
                e = {}
                try:
                    danwei = author['affiliation']
                except Exception:
                    danwei = ""
                e['name'] = author['name']
                e['url'] = url
                sha = e['url'] + '#' + e['name'] + '#' + danwei
                e['sha'] = hashlib.sha1(sha.encode('utf-8')).hexdigest()
                e['ss'] = '人物'
                result.append(e)
        except Exception:
            return result

        return result

    # 关联会议
    def guanLianHuiYi(self, url):
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '活动'
        except Exception:
            return e

        return e

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
            title = content['name']

        except Exception:
            title = ""

        return title

    # 获取所在单位
    def getDanWei(self, content):
        try:
            title = content['affiliation']

        except Exception:
            title = ""

        return title

    # 获取正文
    def getZhengWen(self, content):
        try:
            zhengwen = '\n'.join(content['bio']['p'])

        except Exception:
            zhengwen = ""

        return zhengwen

    # 获取标识
    def getBiaoShi(self, content):
        try:
            pic = 'https://ieeexplore.ieee.org' + content['bio']['graphic']

        except Exception:
            pic = ""

        return pic

    # 获取ORCID
    def getORCID(self, content):
        try:
            orcid = content['orcid']

        except Exception:
            orcid = ""

        return orcid

    # 获取ID
    def getID(self, content):
        try:
            id = content['id']

        except Exception:
            id = ""

        return id

    # 图片关联人物
    def guanLianRenWu(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '人物'
        except Exception:
            return e

        return e


    # ===============================获取会议实体字段值

    # 获取标题
    def getTitle(self, content):
        try:
            title = content['displayTitle']

        except Exception:
            title = ""

        return title

    # 获取举办时间
    def getJuBanShiJian(self, content):
        return_dict = {}
        try:
            return_dict['Y'] = content['currentIssue']['year']
        except Exception:
            return return_dict

        try:
            return_dict['M'] = content['currentIssue']['month']
        except Exception:
            return return_dict

        return return_dict

    # 获取学科类别
    def getXueKeLeiBie(self, content):
        try:
            xueke_list = []
            topics = content['pubTopics']
            for topic in topics:
                xueke_list.append(topic['name'])
            xueKeLeiBie = '|'.join(xueke_list)
        except Exception:
            xueKeLeiBie = ""

        return xueKeLeiBie

    # 获取所在地内容
    def getSuoZaiDi(self, content):
        try:
            for topic in content['facets']:
                if topic['id'] in 'ConferenceLocation':
                    facet_list = []
                    for facet in topic['children']:
                        facet_list.append(facet['name'])
                    suozaidi = '|'.join(facet_list)
                    return suozaidi
                else:
                    continue
            else:
                return ""

        except Exception:
            return ""

class QiKanLunWen_LunWenServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取script标签中的内容
    def getScript(self, resp):
        selector = Selector(text=resp)
        try:
            script_text = selector.xpath(
                "//script[contains(text(),'global.document.metadata')]/text()").extract_first().strip()
            script = re.sub(r";$", "",
                            re.sub(r".*global\.document\.metadata=", "", re.sub(r"[\n\r\t]", "", script_text)))
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

    # 获取期刊详情页，post参数，起止日期
    def getQiKanProfile(self, content):
        return_list = []
        try:
            records = content['records']
            # 获取当前期刊
            for record in records:
                profile = {}
                profile['number'] = record['publicationNumber']
                profile['url'] = 'https://ieeexplore.ieee.org/xpl/aboutJournal.jsp?punumber=' + profile['number']
                profile['qiZhiShiJian'] = record['allYears']
                return_list.append(profile)

            # 获取历史期刊
            for record in records:
                try:
                    for qikan in record['titleHistory']:
                        journal = {}
                        journal['number'] = qikan['publicationNumber']
                        journal['url'] = 'https://ieeexplore.ieee.org/xpl/aboutJournal.jsp?punumber=' + journal['number']
                        try:
                            journal['qiZhiShiJian'] = qikan['startYear'] + ' - ' + qikan['endYear']
                        except Exception:
                            journal['qiZhiShiJian'] = ''
                        return_list.append(journal)
                except Exception:
                    pass

        except Exception:
            return return_list

        return return_list

    # 获取期刊论文列表页接口url，post参数，学科类别
    def getCatalogUrl(self, content, url):
        return_list = []
        try:
            for issues in content['issuelist']:
                for year in issues['years']:
                    for issue in year['issues']:
                        return_dict = {}
                        return_dict['punumber'] = issue['publicationNumber']
                        return_dict['isnumber'] = issue['issueNumber']
                        return_dict['url'] = 'https://ieeexplore.ieee.org/rest/search/pub/' + str(return_dict['punumber']) + '/issue/' + str(return_dict['isnumber']) + '/toc'
                        return_dict['parenUrl'] = url['url']
                        return_list.append(return_dict)

        except Exception:
            return return_list

        return return_list

    # 获取期刊论文详情页
    def getLunWenProfile(self, content, qikan):
        return_list = []
        try:
            records = content['records']
            for record in records:
                profile_dict = {}
                profile_dict['lunwenNumber'] = record['articleNumber']
                profile_dict['qiKanUrl'] = qikan
                try:
                    profile_dict['lunwenUrl'] = 'https://ieeexplore.ieee.org' + record['documentLink']
                except Exception:
                    profile_dict['lunwenUrl'] = 'https://ieeexplore.ieee.org/document/' + record['articleNumber']
                try:
                    profile_dict['title'] = record['articleTitle']
                except Exception:
                    profile_dict['title'] = ''
                try:
                    profile_dict['pdfUrl'] = 'https://ieeexplore.ieee.org' + record['pdfLink']
                except Exception:
                    profile_dict['pdfUrl'] = ''
                try:
                    profile_dict['daXiao'] = record['pdfSize']
                except Exception:
                    profile_dict['daXiao'] = ''
                return_list.append(profile_dict)

        except Exception:
            return return_list

        return return_list

    # 是否有下一页
    def totalPages(self, content):
        try:
            totalPage = content['totalPages']
            if totalPage > 1:
                totalPages = totalPage
            else:
                totalPages = None
        except:
            totalPages = None

        return totalPages

    # ================================= 获取期刊论文实体字段值

    # 获取字段
    def getField(self, script, para):
        text_dict = script
        try:
            if text_dict:
                fieldValue = str(text_dict[para]).strip()
            else:
                fieldValue = ""
        except Exception:
            fieldValue = ""

        return fieldValue

    # 获取期号
    def getQiHao(self, script):
        text_dict = script
        try:
            volume = "Volume:" + str(text_dict['volume']).strip()
        except Exception:
            volume = ""
        try:
            issue = "Issue:" + str(text_dict['issue']).strip()
        except Exception:
            issue = ""
        try:
            date = str(text_dict['publicationDate']).strip()
        except Exception:
            date = ""

        qihao_list = [volume, issue, date]
        return_list = [i for i in qihao_list if i != '']
        return_str = '，'.join(return_list)

        return return_str

    # 获取ISBN、ISSN
    def getGuoJiField(self, script, para):
        text_dict = script
        try:
            return_dict = {}
            fields = text_dict[para]
            for field in fields:
                return_dict[field['format']] = field['value']

        except Exception:
            return_dict = ""

        return return_dict

    # 获取作者/赞助商/学科类别
    def getPeople(self, script, para):
        text_dict = script
        try:
            author_list = []
            authors = text_dict[para]
            for author in authors:
                author_list.append(author['name'])
            zuozhe = '|'.join(author_list)

        except Exception:
            zuozhe = ''

        return zuozhe

    # 获取基金
    def getJiJin(self, script):
        text_dict = script
        try:
            jijin_list = []
            jijins = text_dict['fundingAgencies']['fundingAgency']
            for jijin in jijins:
                jijin_list.append(jijin['fundingName'])
            zuozhe = '|'.join(jijin_list)

        except Exception:
            zuozhe = ''

        return zuozhe

    # 获取关键词
    def getGuanJianCi(self, script):
        try:
            keyword_list = []
            keywords = script['keywords']
            for keyword in keywords:
                keyword_list.extend(keyword['kwd'])
            guanjianci = '|'.join(keyword_list)

        except Exception:
            guanjianci = ''

        return guanjianci

    # 获取时间
    def getShiJian(self, script):
        try:
            return_dict = {}
            return_dict['Y'] = script['publicationYear']
        except Exception:
            return_dict = ""

        return return_dict

    # 获取页数
    def getYeShu(self, script):
        try:
            yeShu = script['startPage'] + ' - ' + script['endPage']

        except Exception:
            yeShu = ""

        return yeShu

    # 是否有参考/引证文献
    def hasWenXian(self, script, para):
        try:
            cankaowenxian = script['sections'][para]

        except Exception:
            cankaowenxian = ""

        return cankaowenxian

    # 参考文献
    def canKaoWenXian(self, content):
        return_list = []
        try:
            for reference in content['references']:
                return_dict = {}
                try:
                    return_dict['序号'] = reference['order']
                except Exception:
                    return_dict['序号'] = ""
                try:
                    return_dict['内容'] = reference['text']
                except Exception:
                    return_dict['内容'] = ""
                try:
                    return_dict['链接'] = 'https://ieeexplore.ieee.org' + reference['links']['documentLink']
                except Exception:
                    return_dict['链接'] = ""

                return_list.append(return_dict)

        except Exception:
            return return_list

        return return_list

    # 引证文献
    def yinZhengWenXian(self, content):
        return_list = []
        try:
            for citations in content['paperCitations'].values():
                for citation in citations:
                    return_dict = {}
                    try:
                        return_dict['序号'] = citation['order']
                    except Exception:
                        return_dict['序号'] = ""
                    try:
                        return_dict['内容'] = citation['displayText']
                    except Exception:
                        return_dict['内容'] = ""
                    try:
                        return_dict['链接'] = 'https://ieeexplore.ieee.org' + citation['links']['documentLink']
                    except Exception:
                        return_dict['链接'] = ""

                    return_list.append(return_dict)

        except Exception:
            return return_list

        return return_list

    # 关联作者
    def guanLianZuoZhe(self, script, url):
        result = []
        try:
            for author in script['authors']:
                e = {}
                try:
                    danwei = author['affiliation']
                except Exception:
                    danwei = ""
                e['name'] = author['name']
                e['url'] = url
                sha = e['url'] + '#' + e['name'] + '#' + danwei
                e['sha'] = hashlib.sha1(sha.encode('utf-8')).hexdigest()
                e['ss'] = '人物'
                result.append(e)
        except Exception:
            return result

        return result

    # 关联期刊
    def guanLianQiKan(self, url):
        e = {}
        try:
            e['url'] = url
            e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
            e['ss'] = '期刊'
        except Exception:
            return e

        return e

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
            title = content['name']

        except Exception:
            title = ""

        return title

    # 获取所在单位
    def getDanWei(self, content):
        try:
            title = content['affiliation']

        except Exception:
            title = ""

        return title

    # 获取正文
    def getZhengWen(self, content):
        try:
            zhengwen = '\n'.join(content['bio']['p'])

        except Exception:
            zhengwen = ""

        return zhengwen

    # 获取标识
    def getBiaoShi(self, content):
        try:
            pic = 'https://ieeexplore.ieee.org' + content['bio']['graphic']

        except Exception:
            pic = ""

        return pic

    # 获取ORCID
    def getORCID(self, content):
        try:
            orcid = content['orcid']

        except Exception:
            orcid = ""

        return orcid

    # 获取ID
    def getID(self, content):
        try:
            id = content['id']

        except Exception:
            id = ""

        return id

    # 图片关联人物
    def guanLianRenWu(self, url, sha):
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '人物'
        except Exception:
            return e

        return e

# =======================================获取期刊实体字段
    # 获取标题/影响因子/特征因子/论文影响分值/频率
    def getValue(self, content, para):
        try:
            title = content[para]

        except Exception:
            title = ""

        return title

    # 获取摘要
    def getZhaiYao(self, content):
        try:
            zhai = str(content['aimsAndScope']).replace('src="../', 'src="https://ieeexplore.ieee.org/')
            zhaiyao = re.sub(r"[\n\r\t]", "", zhai)

        except Exception:
            zhaiyao = ""

        return zhaiyao

    # 获取ISSN
    def getIssn(self, selector):
        try:
            iss = selector.xpath("//strong[contains(text(), 'ISSN')]/..//text()").extract()
            issn = ''.join(iss).replace('ISSN:', '').strip()

        except Exception:
            issn = ""

        return issn

    # 获取详情
    def getDetails(self, content):
        try:
            details = content['publicationDetailsLink']

        except Exception:
            details = ""

        return details

    # 获取出版社/出版信息
    def getXuLie(self, selector, para):
        return_list = []
        try:
            value_list = selector.xpath("//strong[contains(text(), '" + para + "')]/../following-sibling::ul[1]//a")
            for zanzhu in value_list:
                zan_dict = {}
                zan_dict['标题'] = zanzhu.xpath("./text()").extract_first().strip()
                zan_dict['链接'] = zanzhu.xpath("./@href").extract_first().strip()
                return_list.append(zan_dict)


        except Exception:
            return return_list

        return return_list

    # 获取联系方式
    def getLianXiFangShi(self, content):
        try:
            lianxi = content['publicationDetailsLink']
            value_list = lianxi.split("\n\n")
            for i in value_list:
                if 'Editor-in-Chief' in i:
                    lianxifangshi = i.replace('\n', '')
                    break
            else:
                lianxifangshi = ""

        except Exception:
            lianxifangshi = ""

        return lianxifangshi

    # 获取学科类别
    def getXueKeLeiBie(self, content):
        try:
            xueke_list = []
            topics = content['pubTopics']
            for topic in topics:
                xueke_list.append(topic['name'])
            xueKeLeiBie = '|'.join(xueke_list)
        except Exception:
            xueKeLeiBie = ""

        return xueKeLeiBie
