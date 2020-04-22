# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import random
import ast
import json
import copy
import hashlib
from lxml import html
from lxml.html import fromstring, tostring
from urllib import parse
from scrapy.selector import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree

# 父类，有公共属性和方法
class Service(object):
    def __init__(self, logging):
        self.logging = logging

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)


class XueWeiLunWen_xueWeiShouYuDanWei(Service):

    def getIndexUrlData(self):
        data = {
            'productcode': 'CDMD',
            'index': 1,
            'random': random.random()
        }

        return data

    # 获取分类参数
    def getFenLeiDataList(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//dd/a")
            for a in a_list:
                totalCount = a.xpath("./text()").extract_first()
                onclick = a.xpath("./@onclick").extract_first()
                save_data = {}
                save_data['data'] = re.findall(r"naviSearch(\(.*\));", onclick, re.S)[0]
                save_data['totalCount'] = re.findall(r"\((\d+)\)", totalCount, re.S)[0]
                # 列表页首页
                save_data['num'] = 1
                return_data.append(save_data)

        except Exception:
            return return_data

        return return_data

    # 生成单位列表页参数
    def getDanWeiListUrlData(self, data, page):
        return_data = {}
        data_tuple = ast.literal_eval(data)
        name = data_tuple[1]
        value = data_tuple[2]
        return_data['SearchStateJson'] = json.dumps(
            {"StateID": "",
            "Platfrom": "",
            "QueryTime": "",
            "Account": "knavi",
            "ClientToken": "",
            "Language": "",
            "CNode": {"PCode": "CDMD",
                      "SMode": "",
                      "OperateT": ""},
            "QNode": {"SelectT": "",
                      "Select_Fields": "",
                      "S_DBCodes": "",
                      "QGroup": [
                          {"Key": "Navi",
                           "Logic": 1,
                           "Items": [],
                           "ChildItems": [
                               {"Key": "PPaper",
                                "Logic": 1,
                                "Items": [{"Key": 1,
                                         "Title": "",
                                         "Logic": 1,
                                         "Name": "{}".format(name),
                                         "Operate": "",
                                         "Value": "{}?".format(value),
                                         "ExtendType": 0,
                                         "ExtendValue": "",
                                         "Value2": ""}],
                                "ChildItems": []}
                           ]}
                      ],
                      "OrderBy": "RT|",
                      "GroupBy": "",
                      "Additon": ""}
            })
        return_data['displaymode'] = 1
        return_data['pageindex'] = page
        return_data['pagecount'] = 21
        return_data['index'] = 1
        return_data['random'] = random.random()

        return return_data

    # 生成学位授予单位总页数
    def getPageNumber(self, totalCount):
        if int(totalCount) % 21 == 0:
            return int(int(totalCount) / 21)

        else:
            return int(int(totalCount) / 21) + 1

    # 获取单位数量
    def getDanWeiNumber(self, resp):
        selector = Selector(text=resp)
        try:
            number_data = selector.xpath("//em[@id='lblPageCount']/text()").extract_first()
            return number_data

        except Exception:
            return 0

    # 获取单位url
    def getDanWeiUrlList(self, resp, value):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//ul[@class='list_tup']/li/a")
            if a_list:
                for a in a_list:
                    try:
                        href = a.xpath("./@href").extract_first().strip()

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
                        url = 'https://navi.cnki.net/knavi/PPaperDetail?pcode={}&logo={}'.format(pcode, logo)
                        return_data.append({'url': url, 'value': value})

                    except Exception:
                        continue
        except Exception:
            return return_data

        return return_data

    # ==================================== DATA
    def geTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title = selector.xpath("//h3[@class='titbox']/text()").extract_first().strip()

        except Exception:
            title = ''

        return title

    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            fieldValue = selector.xpath("//p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()

        except Exception:
            fieldValue = ''

        return fieldValue

    def getZhuYe(self, resp):
        selector = Selector(text=resp)
        try:
            fieldValue = selector.xpath("//p[contains(text(), '官方网址')]/span/a/text()").extract_first().strip()

        except Exception:
            fieldValue = ''

        return fieldValue

    def getTuPian(self, resp):
        selector = Selector(text=resp)
        try:
            pic = 'https:' + selector.xpath("//dt[contains(@class, 'pic')]/img/@src").extract_first().strip()

        except Exception:
            pic = ''

        return pic

    def getBiaoQian(self, resp):
        selector = Selector(text=resp)
        try:
            tag_list = selector.xpath("//h3[@class='titbox']/span/text()").extract()
            tag = '|'.join(tag_list)

        except Exception:
            tag = ''

        return tag

    def guanLianDanWei(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '机构'

        return e

class XueWeiLunWen_LunWen(Service):
    # 生成专业列表页请求参数
    def getXueKeZhuanYe(self, url):
        pcode = re.findall(r"pcode=(.*?)&", url)[0]
        baseID = re.findall(r"logo=(.*)", url)[0]
        url = 'https://navi.cnki.net/knavi/PPaperDetail/GetSubject?pcode={}&baseID={}&scope=%25u5168%25u90E8'.format(
            pcode, baseID)

        return url

    # 获取专业列表
    def getZhuanYeList(self, resp, value):
        return_data = []
        selector = Selector(text=resp)
        try:
            li_list = selector.xpath("//li[not(@class)]")
            for li in li_list:
                title1 = li.xpath("./h1/a/@title").extract_first()
                dl_list = li.xpath("./div/dl")
                if not dl_list:
                    dict_data = {}
                    id = li.xpath("./h1/a/@id").extract_first()
                    if id:
                        dict_data['s_zhuanYe'] = title1
                        dict_data['zhuanYeId'] = id
                        dict_data['value'] = value
                        return_data.append(dict_data)
                for dl in dl_list:
                    title2 = dl.xpath(".//b[@class='blue']/@title").extract_first()
                    a_list = dl.xpath(".//span/a")
                    if not a_list:
                        dict_data = {}
                        id = li.xpath(".//b[@class='blue']/@id").extract_first()
                        if id:
                            dict_data['s_zhuanYe'] = title1 + '_' + title2
                            dict_data['zhuanYeId'] = id
                            dict_data['value'] = value
                            return_data.append(dict_data)
                    for a in a_list:
                        save_data = {}
                        title3 = a.xpath("./@title").extract_first()
                        zhuanYe = title1 + '_' + title2 + '_' + title3
                        id = a.xpath("./@id").extract_first()

                        if zhuanYe and id:
                            save_data['s_zhuanYe'] = zhuanYe
                            save_data['zhuanYeId'] = id
                            save_data['value'] = value
                            return_data.append(save_data)

        except Exception:
            return return_data

        return return_data

    # 获取论文列表首页post参数
    def getZhuanYeData(self, url, data):
        payload = {
            'pcode': re.findall(r"pcode=(.*?)&", url)[0],
            'baseID': re.findall(r"logo=(.*)", url)[0],
            'subCode': data['zhuanYeId'],
            'orderBy': 'RT|DESC',
            'scope': '%u5168%u90E8'
        }

        return payload

    # 获取总页数
    def getPageNumber(self, resp):
        selector = Selector(text=resp)
        if selector.xpath("//input[@id='pageCount']/@value"):
            total_page = selector.xpath("//input[@id='pageCount']/@value").extract_first()
        else:
            total_page = 1

        return int(total_page)

    # 生成论文列表翻页post参数
    def getLunWenPageData(self, task, page, zhuanye_id):
        payload = {}
        payload['pcode'] = re.findall(r"pcode=(.*?)&", task)[0]
        payload['baseID'] = re.findall(r"logo=(.*)", task)[0]
        payload['subCode'] = zhuanye_id
        payload['scope'] = '%u5168%u90E8'
        payload['orderBy'] = 'RT|DESC'
        payload['pIdx'] = page

        return payload

    # 获取论文详情页及相关字段
    def getProfileUrl(self, resp, zhuanye, parent_url):
        return_data = []
        selector = Selector(text=resp)

        tr_list = selector.xpath("//tr[@class]")

        for tr in tr_list:
            save_data = {}
            td_list = tr.xpath("./td")

            # 获取论文种子
            if td_list[1].xpath('./a/@href'):
                href = td_list[1].xpath('./a/@href').extract_first().strip()
                if re.findall(r"dbCode=(.*?)&", href):
                    dbcode = re.findall(r"dbCode=(.*?)&", href, re.I)[0]
                elif re.findall(r"dbCode=(.*)", href):
                    dbcode = re.findall(r"dbCode=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"fileName=(.*?)&", href):
                    filename = re.findall(r"fileName=(.*?)&", href, re.I)[0]
                elif re.findall(r"fileName=(.*)", href):
                    filename = re.findall(r"fileName=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"tableName=(.*?)&", href):
                    dbname = re.findall(r"tableName=(.*?)&", href, re.I)[0]
                elif re.findall(r"tableName=(.*)", href):
                    dbname = re.findall(r"tableName=(.*)", href, re.I)[0]
                else:
                    continue

                save_data['url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname
            else:
                save_data['url'] = ''

            # 获取时间
            if td_list[5].xpath('./text()'):
                shijian = td_list[5].xpath('./text()').extract_first().strip()
                save_data['shiJian'] = {"v": shijian, "u": "年"}
            else:
                save_data['shiJian'] = {"v": "", "u": "年"}

            # 获取学位类型
            if td_list[6].xpath('./text()'):
                save_data['xueWeiLeiXing'] = td_list[6].xpath('./text()').extract_first().strip()
            else:
                save_data['xueWeiLeiXing'] = ''

            # 获取下载次数
            if td_list[8].xpath('./text()'):
                save_data['xiaZaiCiShu'] = td_list[8].xpath('./text()').extract_first().strip()
            else:
                save_data['xiaZaiCiShu'] = ''

            save_data['s_zhuanYe'] = zhuanye
            save_data['parentUrl'] = parent_url

            return_data.append(save_data)

        return return_data

    # ========================================= DATA
    def getTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title = selector.xpath("//h2[@class='title']/text()").extract_first().strip()
        except Exception:
            title = ''

        return title

    def getZuoZhe(self, resp):
        selector = Selector(text=resp)
        try:
            zuozhe_list = selector.xpath("//div[@class='author']/span/a/text()").extract()
            zuozhe = '|'.join(zuozhe_list)
        except Exception:
            zuozhe = ''

        return zuozhe

    def getZuoZheDanWei(self, resp):
        selector = Selector(text=resp)
        try:
            danwei_list = selector.xpath("//div[@class='orgn']/span/a/text()").extract()
            danwei = '|'.join(danwei_list)
        except Exception:
            danwei = ''

        return danwei

    def getZhaiYao(self, resp):
        selector = Selector(text=resp)
        try:
            zhaiyao = selector.xpath("//span[@id='ChDivSummary']").extract_first()
            html_value = re.sub(r"[\r\n\t]", "", zhaiyao).strip()

        except Exception:
            html_value = ''

        return html_value

    def getMoreFields(self, resp, para):
        data_list = []
        selector = Selector(text=resp)
        try:
            if selector.xpath("//label[contains(text(), '" + para + "')]/../a"):
                value_list = selector.xpath("//label[contains(text(), '" + para + "')]/../a/text()").extract()
                for v in value_list:
                    data_list.append(v.strip())
                value = re.sub(r"[;；]", "", '|'.join(data_list))
            else:
                values = selector.xpath("//label[contains(text(), '" + para + "')]/../text()").extract_first().strip()
                value = re.sub(r"[;；]", "|", re.sub(r"[;；]$", "", values))
                value_list = value.split('|')
                for v in value_list:
                    data_list.append(v.strip())
                value = '|'.join(data_list)

        except Exception:
            value = ''

        return value

    # 获取文内图片
    def getPicUrl(self, resp, fetch):
        return_data = []
        selector = Selector(text=resp)
        data = selector.xpath("//a[@class='btn-note']/@href").extract_first()
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*?)&", data)[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(str(fnbyIdAndName))
            # 获取图片参数
            image_data_resp = fetch(url=image_data_url, method='GET')
            if not image_data_resp:
                self.logging.error('图片参数获取失败, url: {}'.format(image_data_url))
                return return_data
            image_data_response = image_data_resp.content.decode('utf-8')
            print(image_data_response)
            try:
                img_para = re.findall(r"var oJson={'IDs':'(.*)'}", image_data_response)[0]
                if img_para:
                    index_list = img_para.split('||')
                    for index in index_list:
                        image_data = {}
                        url_data = re.findall(r"(.*)##", index)[0]
                        image_title = re.findall(r"##(.*)", index)[0]
                        image_url = 'https://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                        image_data['url'] = image_url
                        image_data['title'] = image_title
                        return_data.append(image_data)

                    return return_data
                else:
                    return return_data

            except:
                return return_data
        else:
            return return_data

    # 关联组图
    def guanLianPics(self, url, sha):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '组图'
        except Exception:
            return e

        return e

    # 关联论文
    def guanLianLunWen(self, url, sha):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e

    # 获取组图
    def getPics(self, imgData):
        labelObj = {}
        return_pics = []
        try:
            if imgData:
                for img in imgData:
                    if img['url']:
                        picObj = {
                            'url': img['url'],
                            'title': img['title'],
                            'desc': ""
                        }
                        return_pics.append(picObj)
                labelObj['全部'] = return_pics
        except Exception:
            labelObj['全部'] = []

        return labelObj

    def getYeShu(self, resp):
        selector = Selector(text=resp)
        try:
            value = selector.xpath("//label[contains(text(), '页数')]/../b/text()").extract_first().strip()
            yeshu = {'v': value, 'u': '页'}
        except Exception:
            yeshu = ''

        return yeshu

    def getDaXiao(self, resp):
        selector = Selector(text=resp)
        try:
            values = selector.xpath("//label[contains(text(), '大小')]/../b/text()").extract_first().strip()
            v = re.findall(r"\d+", values)[0]
            try:
                u = re.findall(r"\D$", values)[0]
            except:
                u = 'K'

            daxiao = {'v': v, 'u': u}

        except Exception:
            daxiao = ''

        return daxiao

    def getUrl(self, resp, para):
        selector = Selector(text=resp)
        try:
            url = selector.xpath("//a[contains(text(), '" + para + "')]/@href").extract_first().strip()
            if re.match(r"http", url):
                href = url
            else:
                href = 'https://kns.cnki.net' + url

        except Exception:
            href = ''

        return href

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
            type_name = div.xpath("./div[@class='dbTitle']/text()").extract_first()
            if keyword in type_name:
                return True
            else:
                return False

        except:
            return False

    # 获取关联参考文献
    def canKaoWenXian(self, url, download):
        return_data = []
        # =================正式============================
        if re.findall(r"dbcode=(.*?)&", url, re.I):
            dbcode = re.findall(r"dbcode=(.*?)&", url, re.I)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url, re.I)[0]
        else:
            return return_data

        if re.findall(r"filename=(.*?)&", url, re.I):
            filename = re.findall(r"filename=(.*?)&", url, re.I)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url, re.I)[0]
        else:
            return return_data

        if re.findall(r"dbname=(.*?)&", url, re.I):
            dbname = re.findall(r"dbname=(.*?)&", url, re.I)[0]
        elif re.findall(r"dbname=(.*)", url, re.I):
            dbname = re.findall(r"dbname=(.*)", url, re.I)[0]
        else:
            return return_data

        # 'https://kns.cnki.net/kcms/detail/frame/list.aspx?dbcode=CMFD&filename=2009014335.nh&dbname=CMFD2009&RefType=1&vl='
        # 'https://kns.cnki.net/kcms/detail/frame/list.aspx?dbcode=CMFD&filename=2009014335.nh&dbname=CMFD2009&RefType=3&vl='
        # ================================================
        index_url = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                     'dbcode={}'
                     '&filename={}'
                     '&dbname={}'
                     '&RefType=1'
                     '&vl=')

        canKaoUrl = index_url.format(dbcode, filename, dbname)
        # 获取参考文献页源码
        canKaoResp = download(url=canKaoUrl, method='GET')
        if not canKaoResp:
            self.logging.error('参考文献接口页响应失败, url: {}'.format(canKaoUrl))
            return

        response = canKaoResp.text
        selector = Selector(text=response)
        div_list = selector.xpath("//div[@class='essayBox']")
        i = -1
        for div in div_list:
            leixing_dict = {}
            i += 1
            # 获取实体类型
            shiTiLeiXing = div.xpath("./div[@class='dbTitle']/text()").extract_first()
            # print(shiTiLeiXing)
            # 获取CurDBCode参数
            CurDBCode = re.findall(r"pc_(.*)", div.xpath("./div[@class='dbTitle']/b/span/@id").extract_first())[0]
            # 获取该类型总页数
            article_number = int(div.xpath("./div[@class='dbTitle']/b/span/text()").extract_first())
            if article_number % 10 == 0:
                page_number = int(article_number / 10)
            else:
                page_number = int((article_number / 10)) + 1

            # 题录
            if '题录' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '题录'
                lexing_list = []
                # pass
                # # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    leiXingResp = leiXingResp.content.decode('utf-8')
                    selector = Selector(text=leiXingResp)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data["标题"] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp;)', '', li.xpath("./a/text()").extract_first())).strip()
                            except:
                                data["标题"] = ""
                            try:
                                data["其它信息"] = re.sub(r'^.', '', re.sub(r'\s+', ' ', re.sub(r'[\r\n\t]', '', li.xpath("./text()").extract_first()))).strip()
                            except:
                                data["其他信息"] = ""

                            lexing_list.append(data)

                leixing_dict['题录'] = lexing_list

            elif '学术期刊' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '学术期刊'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp)', '', li.xpath("./a[@target='kcmstarget']/text()").extract_first())).strip()
                            except:
                                data['标题'] = ""
                            try:
                                zuoZhe = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp)', '', li.xpath("./text()").extract_first())).strip()
                                data['作者'] = re.sub('[,，]', '|', ''.join(re.findall(r'\.(.*?)\.', zuoZhe))).strip()
                            except:
                                data['作者'] = ""
                            try:
                                data['刊名'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp)', '', li.xpath("./a[2]/text()").extract_first())).strip()
                            except:
                                data['刊名'] = ""
                            try:
                                data['年卷期'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp;)', '', li.xpath("./a[3]/text()").extract_first())).strip()
                            except:
                                data['年卷期'] = ""

                            lexing_list.append(data)

                leixing_dict['期刊论文'] = lexing_list

            elif '国际期刊' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '国际期刊'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t|&nbsp)', '', li.xpath("./a/text()").extract_first())).strip()
                            except:
                                data['标题'] = ""
                            try:
                                try:
                                    year = re.findall(r"(\d{4})", li.xpath("./text()").extract_first())[0].strip()
                                except:
                                    year = ""
                                try:
                                    qi = re.findall(r"(\(.*\))", li.xpath("./text()").extract_first())[0].strip()
                                except:
                                    qi = ""
                                if year:
                                    data['年卷期'] = year + qi
                                else:
                                    data['年卷期'] = ""
                            except:
                                data['年卷期'] = ""
                            try:
                                zuozhe = re.findall(r'\.\s*(.*)\s*\.&nbsp', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t)', '', li.xpath("./text()").extract_first())))[0].strip()
                                data['作者'] = re.sub(r"[,，]", "|", zuozhe).strip()
                            except:
                                data['作者'] = ''
                            try:
                                data['刊名'] = re.sub(r"&nbsp", "", re.findall(r'&nbsp\s*(.*)\s*\.', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|\t)', '', li.xpath("./text()").extract_first())))[0]).strip()
                            except:
                                data['刊名'] = ""
                            try:
                                data['链接'] = 'http://kns.cnki.net' + li.xpath("./a/@href").extract_first()
                            except:
                                data['链接'] = ''

                            lexing_list.append(data)

                leixing_dict['外文文献'] = lexing_list

            elif '图书' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '图书'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['其它信息'] = re.sub(r'\s+', ' ', re.sub('.*\[M\]\.', '', ''.join(re.findall(r"[^&nbsp\r\n]", li.xpath("./text()").extract_first())))).strip()
                            except:
                                data['其他信息'] = ""
                            try:
                                data['标题'] = re.findall(r"(.*)\[M\]", re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()").extract_first()))[0].strip()
                            except:
                                data['标题'] = ""

                            lexing_list.append(data)

                leixing_dict['图书'] = lexing_list

            elif '学位' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '学位'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a[@target='kcmstarget']/text()").extract_first())).strip()
                            except:
                                data['标题'] = ""
                            try:
                                re_time = re.compile("\d{4}")
                                data['时间'] = [re.findall(re_time, time)[0] for time in li.xpath(".//text()").extract() if re.findall(re_time, time)][0].strip()
                            except:
                                data['时间'] = ""
                            try:
                                data['作者'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', re.findall(r"\[D\]\.(.*)\.", li.xpath("./text()").extract_first())[0])).strip()
                            except:
                                data['作者'] = ""
                            try:
                                data['机构'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a[2]/text()").extract_first())).strip()
                            except:
                                data['机构'] = ""

                            lexing_list.append(data)

                leixing_dict['学位论文'] = lexing_list

            elif '标准' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '标准'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标准号'] = ''.join(re.findall(r"[^\r\n]", li.xpath("./text()").extract_first())).strip()
                            except:
                                data['标准号'] = ''
                            try:
                                data['标题'] = ''.join(re.findall(r"[^\r\n\.]", li.xpath("./a/text()").extract_first())).strip()
                            except:
                                data['标题'] = ''
                            try:
                                data['时间'] = ''.join(re.findall(r"S\.*\s*(.*)", li.xpath("./text()").extract()[1])).strip()
                            except:
                                data['时间'] = ''
                            try:
                                url = li.xpath("./a/@href")[0]
                                # 去掉amp;
                                url = re.sub('amp;', '', url)
                                # dbcode替换成dbname
                                url = re.sub('dbcode', 'dbname', url)
                                # 截取参数部分
                                url = re.findall(r"detail\.aspx\?(.*)", url)[0]
                                # 拼接url
                                data['链接'] = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?' + url
                            except:
                                data['链接'] = ''

                            lexing_list.append(data)

                leixing_dict['标准'] = lexing_list

            elif '专利' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '专利'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first())
                            except:
                                data['标题'] = ''
                            try:
                                zuozhe = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath('./text()').extract_first())))[0]
                                data['作者'] = re.sub(',', '|', zuozhe)
                            except:
                                data['作者'] = ''
                            try:
                                data['类型'] = re.findall(r'.*\. (.*?)\:', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath('./text()').extract_first())))[0]
                            except:
                                data['类型'] = ''
                            try:
                                data['公开号'] = re.findall('\:(.*?)\,', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath('./text()').extract_first())))[0]
                            except:
                                data['公开号'] = ''
                            try:
                                data['链接'] = 'http://kns.cnki.net' + li.xpath('./a/@href').extract_first()
                            except:
                                data['链接'] = ''

                            lexing_list.append(data)

                leixing_dict['专利'] = lexing_list

            elif '报纸' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '报纸'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first()))
                            except:
                                data['标题'] = ''
                            try:
                                data['机构'] = re.findall(r'.*\.(.*?)\.', re.sub('\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()").extract_first())))[0]
                            except:
                                data['机构'] = ''
                            try:
                                data['时间'] = re.findall(r'. (\d{4}.*)', re.sub('\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()").extract_first())))[0]
                            except:
                                data['时间'] = ''
                            try:
                                data['链接'] = 'http://kns.cnki.net' + li.xpath('./a/@href').extract_first()
                            except:
                                data['链接'] = ''

                            lexing_list.append(data)

                leixing_dict['报纸'] = lexing_list

            elif '年鉴' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '年鉴'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
                    # 判断参考文献类型页面是否正确
                    status = self._judgeHtml(leiXingDivList, i, keyword)
                    if status is True:
                        leiXingDiv = leiXingDivList[i]
                        li_list = leiXingDiv.xpath(".//li")
                        for li in li_list:
                            data = {}
                            try:
                                # li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                li_string_html = li.extract_first()
                                data['标题'] = re.findall(r'<a onclick="getKns55NaviLink\(.*?\);">(.*)</a>', li_string_html)[0]
                            except:
                                data['标题'] = ''
                            try:
                                data['机构'] = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath('./text()').extract_first())))[0]
                            except:
                                data['机构'] = ''
                            try:
                                li_string_html = html.tostring(doc=li, encoding='utf-8').decode('utf-8')
                                data['时间'] = re.findall(r'<a onclick="getKns55YearNaviLink\(.*?\);">(.*)</a>', li_string_html)[0]
                            except:
                                data['时间'] = ''

                            lexing_list.append(data)

                leixing_dict['年鉴'] = lexing_list

            elif '会议' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '会议'
                lexing_list = []
                # pass
                # 翻页获取
                for page in range(page_number):
                    qiKanLunWenIndexUrl = ('https://kns.cnki.net/kcms/detail/frame/list.aspx?'
                                           'dbcode={}'
                                           '&filename={}'
                                           '&dbname={}'
                                           '&RefType=1'
                                           '&CurDBCode={}'
                                           '&page={}'.format(dbcode, filename, dbname, CurDBCode, page + 1))
                    # 获取该页html
                    leiXingResp = download(url=qiKanLunWenIndexUrl, method='GET')
                    if not leiXingResp:
                        continue

                    resp_text = leiXingResp.text
                    selector = Selector(text=resp_text)
                    leiXingDivList = selector.xpath("//div[@class='essayBox']")
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
                                data['作者'] = re.sub(r"(,|，)", "|", re.findall(r"\[A\]\.(.*?)\.", re.sub(r"(\r|\n|\s+)", "", li.xpath("./text()").extract_first()))[0])
                            except:
                                data['作者'] = ''
                            try:
                                data['文集'] = re.findall(r"\[A\]\..*?\.(.*?)\[C\]", re.sub(r"(\r|\n|\s+)", "", li.xpath("./text()").extract_first()))[0]
                            except:
                                data['文集'] = ''
                            try:
                                data['时间'] = {"Y": re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "", li.xpath("./text()").extract_first()))[0]}
                            except:
                                data['时间'] = {}

                            lexing_list.append(data)

                leixing_dict['会议论文'] = lexing_list

            return_data.append(leixing_dict)

        return return_data

    def guanLianRenWu(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//div[@class='author']/span/a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                              onclick[0],
                              onclick[1],
                              onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        e['ss'] = '人物'
                        return_data.append(e)
                    else:
                        continue

        except Exception:
            return return_data

        return return_data

    def guanLianQiYeJiGou(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//div[@class='orgn']/span/a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                              onclick[0],
                              onclick[1],
                              onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        e['ss'] = '机构'
                        return_data.append(e)
                    else:
                        continue

        except Exception:
            return return_data

        return return_data

    def guanLianDaoShi(self, resp):
        data_list = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//label[contains(text(), '导师')]/../a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                            onclick[0],
                            onclick[1],
                            onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        e['ss'] = '人物'
                        data_list.append(e)
                    else:
                        continue
            else:
                return data_list

        except Exception:
            return data_list

        return data_list

    def guanLianXueWeiShouYuDanWei(self, url):
        e = {}
        if url:
            e['url'] = url
            e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            e['ss'] = '机构'

            return e

        else:
            return e

    def getPeople(self, zuozhe, daoshi, t):
        zuozheList = copy.deepcopy(zuozhe)
        daoshiList = copy.deepcopy(daoshi)
        people_list = zuozheList + daoshiList
        if people_list:
            for people in people_list:
                people['shiJian'] = t

        return people_list

class ZhiWangLunWen_JiGou(Service):
    # ================================= DATA
    # 获取字段值（曾用名、地域）
    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            fValue = selector.xpath("//label[contains(text(), '" + para + "')]/../text()").extract_first().strip()
        except:
            fValue = ''

        return fValue

    # 获取官网地址
    def getGuanWangDiZhi(self, resp):
        selector = Selector(text=resp)
        try:
            url = selector.xpath("//label[contains(text(), '官方网址')]/../a/text()").extract_first().strip()
        except:
            url = ''

        return url

    # 获取机构名
    def getJiGouName(self, resp):
        selector = Selector(text=resp)
        try:
            name = selector.xpath("//h2[@class='name']/text()").extract_first()
        except:
            name = ''

        return name

    # 获取图片
    def getTuPian(self, resp):
        selector = Selector(text=resp)
        try:
            img = selector.xpath("//div[@class='aboutIntro']/p/img/@src").extract_first()
            href = 'https:' + img

        except:
            href = ''

        return href

    # 关联机构
    def guanLianJiGou(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '机构'

        return e

class ZhiWangLunWen_ZuoZhe(Service):
    # =================================== DATA
    def ifEffective(self, resp):
        if '对不起，未找到相关数据' in resp:
            return False

        else:
            return True


    def getSuoZaiDanWei(self, resp, shijian):
        return_data = []
        selector = Selector(text=resp)
        try:
            companies = selector.xpath("//p[@class='orgn']/a/text()").extract()
            if companies:
                for com in companies:
                    com_dict = {}
                    com_dict['所在单位'] = re.sub(r'\s+', ' ', re.sub('r(\r|\n|\t|&nbsp;)', '', com)).strip()
                    com_dict['时间'] = shijian
                    return_data.append(com_dict)

        except:
            return return_data

        return return_data

    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//p[@class='orgn']/a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                              onclick[0],
                              onclick[1],
                              onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        e['ss'] = '机构'
                        return_data.append(e)
                    else:
                        continue

        except Exception:
            return return_data

        return return_data

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
        selector = Selector(text=resp)
        fenlei = selector.xpath("//span[@class='wrap']/text()").extract_first().strip()
        print(fenlei)
        li_list = selector.xpath("//li")
        for li in li_list:
            if li.xpath("./span/a/@title"):
                name1 = li.xpath("./span/a/@title").extract_first()
                a_list = li.xpath('./dl/dd/a')
                for a in a_list:
                    name2 = a.xpath("./@title").extract_first()
                    onclick = ast.literal_eval(re.findall(r"(\(.*\))", a.xpath("./@onclick").extract_first())[0])
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

                    if fenlei == '学科导航':
                        yield {'xueKeLeiBie': name1 + '_' + name2, 'data': data, 'SearchStateJson': SearchStateJson}
                    elif fenlei == '核心期刊导航':
                        yield {'heXinQiKan': name1 + '_' + name2, 'data': data, 'SearchStateJson': SearchStateJson}

    def getPageNumber(self, resp):
        selector = Selector(text=resp)
        if selector.xpath("//em[@class='lblCount']/text()"):
            data_sum = int(selector.xpath("//em[@class='lblCount']/text()").extract_first())
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
        selector = Selector(text=resp)
        li_list = selector.xpath("//ul[@class='list_tup']/li")
        for li in li_list:
            title = li.xpath("./a/@title").extract_first().strip()
            href = li.xpath("./a/@href").extract_first().strip()
            pcode = re.findall(r"pcode=(.*?)&", href)[0]
            pykm = re.findall(r"&baseid=(.*)", href)[0]
            url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)

            yield {'url': url, 'title': title}


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


class HuiYiLunWen_LunWenTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 获取pcode、lwjcode
    def getPcodeAndLwjcode(self, data):
        try:
            pcode = re.findall(r"pcode=(.*?)&", data)[0]
        except:
            pcode = None

        try:
            lwjcode = re.findall(r"lwjcode=(.*?)&", data)[0]
        except:
            lwjcode = None

        return pcode, lwjcode

    # 生成会议数量页url
    def getHuiYiNumberUrl(self, pcode, lwjcode):
        url = 'http://navi.cnki.net/knavi/DpaperDetail/GetDpaperList?pcode={}&lwjcode={}&orderBy=FN&pIdx=0'.format(
            pcode, lwjcode)

        return url

    # 获取会议数量
    def getHuiYiNumber(self, resp):
        selector = Selector(text=resp)
        data = selector.xpath("//span[@id='partiallistcount']/text()").extract_first()
        if data:
            return int(data)
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
        selector = Selector(text=resp)
        a_list = selector.xpath("//td[@class='nobreak']/following-sibling::td[@class='name']/a")
        for a in a_list:
            href = a.xpath("./@href").extract_first()
            if href:
                try:
                    url = 'http://kns.cnki.net/kcms/detail/detail.aspx?' + re.findall(r"\?(.*)", href)[0]
                    return_data.append(url)
                except:
                    continue

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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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





class QiKanLunWen_LunWenDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        # task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        # return ast.literal_eval(task['memo'])
        return ast.literal_eval(task_data)

    # 获取期刊名称
    def getQiKanMingCheng(self, resp):
        response = resp.content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            title = html_etree.xpath("//p[@class='title']/a/text()")[0]
        except:
            title = ""

        return title

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
        if canKaoResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
        response = resp.content.decode('utf-8')
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
                shiJian = re.findall(r'(\d{4})年.*期', str(response))
                if shiJian:
                    return {"Y": shiJian[0]}

                else:
                    return {}

    # 获取页数
    def getYeShu(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
                    name = a.xpath("./text()")[0].strip()

                    return_data.append({'name': name, 'url': url, 'ss': '机构', 'sha': url_sha1})

            return return_data
        else:

            return return_data

    # 获取PDF下载链接
    def getXiaZai(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
        html_etree = etree.HTML(response)
        try:
            p_list = html_etree.xpath("//div[@class='sourinfo']/p")
        except:
            p_list = None
        if p_list:
            p = p_list[2]
            try:
                qiHao = p.xpath("./a/text()")[0]

                return qiHao.strip()

            except:
                qiHao = re.findall(r"(\d{4}年.*期)", html)
                if qiHao:

                    return qiHao[0].strip()
                else:

                    return ""
        else:
            return ""

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
    def getPicUrls(self, download_middleware, resp):
        return_data = []
        response = resp.content.decode('utf-8')
        html_etree = etree.HTML(response)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url, mode='get')
            if image_data_resp['code'] == 0:
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
                        image_data['desc'] = image_title
                        # image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                        return_data.append(image_data)

                    return return_data

                else:
                    return return_data
            else:
                self.logging.error('图片参数获取失败, url: {}'.format(image_data_url))
                return return_data
        else:
            return return_data

    # 获取组图
    def getPics(self, picUrls, title):
        labelObj = {}
        return_pics = []
        try:
            if picUrls:
                for pic in picUrls:
                    picObj = {
                        'url': pic['url'],
                        'title': title,
                        'desc': pic['desc']
                    }
                    return_pics.append(picObj)
            labelObj['全部'] = return_pics
        except Exception:
            labelObj['全部'] = []

        return labelObj

    # 关联组图
    def guanLianPics(self, url, sha):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '组图'
        except Exception:
            return e

        return e

    # 关联论文
    def guanLianLunWen(self, url, sha):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e

    # 获取doi
    def getDoi(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        # task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        # return ast.literal_eval(task['memo'])
        return ast.literal_eval(task_data)

    # 获取标题
    def getArticleTitle(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
        html_etree = etree.HTML(response)
        data = html_etree.xpath("//a[@class='btn-note']/@href")
        if data:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data[0])[0]
            # 图片参数url
            image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)
            # 获取图片参数
            image_data_resp = download_middleware.getResp(url=image_data_url, mode='get')
            if image_data_resp['status'] == 0:
                image_data_response = image_data_resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(response))
        if yeShu:

            return {"v": yeShu[0], "u": "页"}
        else:

            return {}

    # 获取大小
    def getDaXiao(self, resp):
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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
        if canKaoResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
                            if leiXingResp['code'] == 0:
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
            return_data['ss'] = '活动'
            return return_data

        except:
            return return_data


    # 获取关联文集
    def getGuanLianWenJi(self, url):
        return_data = {}
        try:
            save_url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?' + re.findall(r"\?(.*)", url)[0]
            return_data['sha'] = hashlib.sha1(save_url.encode('utf-8')).hexdigest()
            return_data['url'] = save_url
            return_data['ss'] = '期刊'
            return return_data
        except:
            return return_data

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        response = resp.content.decode('utf-8')
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


class ZhiWangLunWen_HuiYiDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):

        # return ast.literal_eval(task_data['memo'])
        return ast.literal_eval(task_data)

    # 获取标题内容
    def getTitle(self, resp, text):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//p[@class='hostUnit']"):
            for p in resp_etree.xpath("//p[@class='hostUnit']"):
                if p.xpath("./text()"):
                    if '{}'.format(text) in p.xpath("./text()")[0]:
                        if p.xpath("./span/text()"):
                            return p.xpath("./span/@title")[0]


        return ""

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

        return ast.literal_eval(task_data)

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
            data = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp;)', '', p_text))

            return data
        except:
            p_text = ''

            return p_text

    def getBiaoShi(self, resp):
        response = bytes(bytearray(resp, encoding='utf-8'))
        html_etree = etree.HTML(response)
        try:
            pic_url = 'http:' + html_etree.xpath("//dt[@id='J_journalPic']/img/@src")[0]

        except Exception:
            pic_url = ""

        return pic_url

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

    # def getLaiYuanShuJuKu(self, resp):
    #     response = bytes(bytearray(resp, encoding='utf-8'))
    #     html_etree = etree.HTML(response)
    #     try:
    #         databases = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[@class='database']/@title")
    #         database = '|'.join(databases)
    #     except:
    #         database = ''
    #
    #     return database

    def getLaiYuanShuJuKu(self, html):
        databases = []
        tree = etree.HTML(html)
        try:
            tags = tree.xpath("//p[@class='database']")
            for tag in tags:
                html_value = re.sub(r"[\n\r\t]", "", tostring(tag).decode('utf-8')).strip()
                databases.append(html_value)
            database = ''.join(databases)

        except Exception:
            database = ""

        return database

    def getQiKanRongYu(self, html):
        databases = []
        tree = etree.HTML(html)
        try:
            tags = tree.xpath("//p[contains(text(), '期刊荣誉')]/following-sibling::p")
            for tag in tags:
                html_value = re.sub(r"[\n\r\t]", "", tostring(tag).decode('utf-8')).strip()
                databases.append(html_value)
            database = ''.join(databases)

        except Exception:
            database = ""

        return database

    def guanLianQiKan(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '期刊'
        return e

    # def getQiKanRongYu(self, resp):
    #     response = bytes(bytearray(resp, encoding='utf-8'))
    #     html_etree = etree.HTML(response)
    #     try:
    #         data = html_etree.xpath("//ul[@id='evaluateInfo']/li[not(@class)]/p[text()='期刊荣誉：']/following-sibling::p[1]/span/text()")[0]
    #     except:
    #         data = ''
    #
    #     return data.replace(';', '|')

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
        response = resp.content.decode('utf-8')
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
        response = resp.content.decode('utf-8')
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


class ZhiWangLunWen_WenJiDataServer(object):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):

        return ast.literal_eval(task_data)

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

    def getGuanLianHuoDong_HuiYi(self, url, ss):
        return {
            'url': url,
            'sha': hashlib.sha1(url.encode('utf-8')).hexdigest(),
            'ss': ss
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
