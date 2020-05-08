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
                        url = 'http://navi.cnki.net/knavi/PPaperDetail?pcode={}&logo={}'.format(pcode, logo)
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
            pic = 'http:' + selector.xpath("//dt[contains(@class, 'pic')]/img/@src").extract_first().strip()

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
        url = 'http://navi.cnki.net/knavi/PPaperDetail/GetSubject?pcode={}&baseID={}&scope=%25u5168%25u90E8'.format(
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
            try:
                href = td_list[1].xpath('./a/@href').extract_first().strip()
                if re.findall(r"dbCode=(.*?)&", href, re.I):
                    dbcode = re.findall(r"dbCode=(.*?)&", href, re.I)[0]
                elif re.findall(r"dbCode=(.*)", href, re.I):
                    dbcode = re.findall(r"dbCode=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"fileName=(.*?)&", href, re.I):
                    filename = re.findall(r"fileName=(.*?)&", href, re.I)[0]
                elif re.findall(r"fileName=(.*)", href, re.I):
                    filename = re.findall(r"fileName=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"tableName=(.*?)&", href, re.I):
                    dbname = re.findall(r"tableName=(.*?)&", href, re.I)[0]
                elif re.findall(r"tableName=(.*)", href, re.I):
                    dbname = re.findall(r"tableName=(.*)", href, re.I)[0]
                else:
                    continue

                save_data['url'] = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname
            except:
                save_data['url'] = ''

            # 获取时间
            try:
                shijian = td_list[5].xpath('./text()').extract_first().strip()
                save_data['shiJian'] = {"v": shijian, "u": "年"}
            except:
                save_data['shiJian'] = ''

            # 获取学位类型
            try:
                save_data['xueWeiLeiXing'] = td_list[6].xpath('./text()').extract_first().strip()
            except:
                save_data['xueWeiLeiXing'] = ''

            # 获取下载次数
            try:
                save_data['xiaZaiCiShu'] = td_list[8].xpath('./text()').extract_first().strip()
            except:
                save_data['xiaZaiCiShu'] = ''

            save_data['s_zhuanYe'] = zhuanye
            save_data['parentUrl'] = parent_url

            return_data.append(save_data)

        return return_data

class LunWen_Data(Service):
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
            if selector.xpath("//div[@class='author']/span/a"):
                zuozhe_list = selector.xpath("//div[@class='author']/span/a/text()").extract()

            else:
                zuozhe_list = selector.xpath("//div[@class='author']/span/text()").extract()

            zuozhe = '|'.join(zuozhe_list)

        except Exception:
            zuozhe = ''

        return zuozhe

    def getZuoZheDanWei(self, resp):
        selector = Selector(text=resp)
        try:
            if selector.xpath("//div[@class='orgn']/span/a"):
                danwei_list = selector.xpath("//div[@class='orgn']/span/a/text()").extract()
            else:
                danwei_list = selector.xpath("//div[@class='orgn']/span/text()").extract()

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

    def getQiKanName(self, resp):
        selector = Selector(text=resp)
        try:
            name = selector.xpath("//p[@class='title']/a/text()").extract_first().strip()

        except Exception:
            name = ''

        return name

    def getQiHao(self, resp):
        selector = Selector(text=resp)
        try:
            qihao = selector.xpath("//div[@class='sourinfo']/p/a[contains(text(), '年')]/text()").extract_first().strip()

        except Exception:
            qihao = ''

        return qihao

    def getYear(self, resp):
        selector = Selector(text=resp)
        try:
            qihao = selector.xpath("//div[@class='sourinfo']/p/a[contains(text(), '年')]/text()").extract_first().strip()
            year = re.findall(r"(\d{4})年?", qihao)[0]

        except Exception:
            year = ''

        return year

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
            # print(image_data_response)
            try:
                img_para = re.findall(r"var oJson={'IDs':'(.*)'}", image_data_response)[0]
                if img_para:
                    index_list = img_para.split('||')
                    for index in index_list:
                        image_data = {}
                        url_data = re.findall(r"(.*)##", index)[0]
                        image_title = re.findall(r"##(.*)", index)[0]
                        image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
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

    def getXiaZai(self, resp):
        selector = Selector(text=resp)
        try:
            xiazai = selector.xpath("//label[contains(text(), '下载')]/../b/text()").extract_first().strip()

        except Exception:
            xiazai = ''

        return xiazai

    def getSuoZaiYeMa(self, resp):
        selector = Selector(text=resp)
        try:
            yema = selector.xpath("//label[contains(text(), '页码')]/../b/text()").extract_first().strip()

        except Exception:
            yema = ''

        return yema

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

    # 获取论文集url
    def getLunWenJiUrl(self, resp):
        if re.findall(r"RegisterSBlock(\(.*?\));", resp, re.I):
            try:
                data = ast.literal_eval(re.findall(r"RegisterSBlock(\(.*?\));", resp, re.I)[0])
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
        selector = Selector(text=resp)
        try:
            wenji_list = selector.xpath("//div[@class='sourinfo']/p//text()").extract()
            wenji = re.sub(r"(\r|\n|\t)", "", ' '.join(wenji_list)).strip()

        except Exception:
            wenji = ''

        return wenji

    def getUrl(self, resp, para):
        selector = Selector(text=resp)
        try:
            url = selector.xpath("//a[contains(text(), '" + para + "')]/@href").extract_first().strip()
            if re.match(r"http", url):
                href = url
            else:
                href = 'http://kns.cnki.net' + url

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

        # 'http://kns.cnki.net/kcms/detail/frame/list.aspx?dbcode=CMFD&filename=2009014335.nh&dbname=CMFD2009&RefType=1&vl='
        # 'http://kns.cnki.net/kcms/detail/frame/list.aspx?dbcode=CMFD&filename=2009014335.nh&dbname=CMFD2009&RefType=3&vl='
        # ================================================
        index_url = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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
                # 判断总页数是否大于50页，大于50页，只翻最后50页
                if page_number > 50:
                    first_page = int(page_number - 50)
                else:
                    first_page = 0
            else:
                page_number = int((article_number / 10)) + 1
                # 判断总页数是否大于50页，大于50页，只翻最后50页
                if page_number > 50:
                    first_page = int(page_number - 50)
                else:
                    first_page = 0

            # 题录
            if '题录' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '题录'
                leixing_list = []
                # pass
                # # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            # 列表去重
                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['题录'] = leixing_list

            elif '学术期刊' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '学术期刊'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['期刊论文'] = leixing_list

            elif '国际期刊' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '国际期刊'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['外文文献'] = leixing_list

            elif '图书' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '图书'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['图书'] = leixing_list

            elif '学位' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '学位'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['学位论文'] = leixing_list

            elif '标准' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '标准'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['标准'] = leixing_list

            elif '专利' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '专利'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['专利'] = leixing_list

            elif '报纸' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '报纸'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['报纸'] = leixing_list

            elif '年鉴' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '年鉴'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['年鉴'] = leixing_list

            elif '会议' in shiTiLeiXing:
                # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                keyword = '会议'
                leixing_list = []
                # pass
                # 翻页获取
                for page in range(first_page, page_number):
                    qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
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
                                data['标题'] = li.xpath("./a/text()").extract_first()
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
                                data['时间'] = re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "", li.xpath("./text()").extract_first()))[0]
                            except:
                                data['时间'] = {}

                            if data not in leixing_list:
                                leixing_list.append(data)

                leixing_dict['会议论文'] = leixing_list

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
                        url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
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
                        url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
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
                        url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
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

    def guanLianWenJi(self, url):
        e = {}
        if url:
            e['url'] = url
            e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            e['ss'] = '期刊'

            return e

        else:
            return e

    def guanLianQiKan(self, url):
        e = {}
        if url:
            e['url'] = url
            e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            e['ss'] = '期刊'

            return e

        else:
            return e

    def guanLianHuoDongHuiYi(self, url):
        e = {}
        if url:
            e['url'] = url
            e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            e['ss'] = '活动'

            return e

        else:
            return e

    def getPeople(self, zuozhe, daoshi, t):
        if zuozhe:
            zuozheList = copy.deepcopy(zuozhe)
        else:
            zuozheList = []
        if daoshi:
            daoshiList = copy.deepcopy(daoshi)
        else:
            daoshiList = []

        people_list = zuozheList + daoshiList
        if people_list:
            for people in people_list:
                people['shiJian'] = t

        return people_list

class HuiYiLunWen_WenJi_HuiYi(Service):
    def getDaoHangPageData(self):
        data = {
            "productcode": "CIPD",
            "ClickIndex": "2",
            "random": random.random()
        }

        return data

    # 获取分类参数
    def getFenLeiDataList(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            li_list = selector.xpath("//ul/li")
            for li in li_list:
                fir_a = li.xpath("./span/a")
                sec_a_list = li.xpath("./dl/dd/a")
                onclick1 = fir_a.xpath("./@onclick").extract_first().strip()
                name1 = fir_a.xpath("./@title").extract_first().strip()
                if not sec_a_list:
                    try:
                        data_dict = {}
                        count1 = fir_a.xpath("./em/text()").extract_first()
                        data_dict['data'] = re.findall(r"naviSearch(\(.*\));", onclick1, re.S)[0]
                        data_dict['totalCount'] = re.findall(r"\((.*)\)", count1, re.S)[0].strip()
                        data_dict['s_hangYe'] = name1
                        # 列表页首页
                        data_dict['num'] = 1
                        return_data.append(data_dict)
                    except Exception:
                        continue

                for a in sec_a_list:
                    try:
                        data_dict = {}
                        onclick2 = a.xpath("./@onclick").extract_first().strip()
                        count2 = a.xpath("./em/text()").extract_first()
                        name2 = a.xpath("./@title").extract_first().strip()
                        data_dict['data'] = re.findall(r"naviSearch(\(.*\));", onclick2, re.S)[0]
                        data_dict['totalCount'] = re.findall(r"\((.*)\)", count2, re.S)[0].strip()
                        data_dict['s_hangYe'] = name1 + '_' + name2
                        # 列表页首页
                        data_dict['num'] = 1
                        return_data.append(data_dict)
                    except Exception:
                        continue

        except Exception:
            return return_data

        return return_data

    # 生成行业列表页文集总页数
    def getPageNumber(self, totalCount):
        if int(totalCount) % 20 == 0:
            return int(int(totalCount) / 20)

        else:
            return int(int(totalCount) / 20) + 1

    # 生成论文集列表页请求参数
    def getLunWenJiUrlData(self, data, page):
        return_data = {}
        data_tuple = ast.literal_eval(data)
        return_data['SearchStateJson'] = json.dumps(
            {
                "StateID": "",
                "Platfrom": "",
                "QueryTime": "",
                "Account": "knavi",
                "ClientToken": "",
                "Language": "",
                "CNode": {"PCode": "CIPD",
                          "SMode": "",
                          "OperateT": ""},
                "QNode": {"SelectT": "",
                          "Select_Fields": "",
                          "S_DBCodes": "",
                          "QGroup": [{"Key": "Navi",
                                      "Logic": 1,
                                      "Items": [],
                                      "ChildItems": [{"Key": "DPaper1",
                                                      "Logic": 1,
                                                      "Items": [{"Key": 1,
                                                                 "Title": "",
                                                                 "Logic": 1,
                                                                 "Name": "行业分类代码",
                                                                 "Operate": "",
                                                                 "Value": "{}?".format(data_tuple[2]),
                                                                 "ExtendType": 0,
                                                                 "ExtendValue": "",
                                                                 "Value2": ""}],
                                                      "ChildItems": []}]}],
                          "GroupBy": "",
                          "Additon": ""}
            }
        )
        return_data['displaymode'] = 1
        return_data['pageindex'] = page
        return_data['pagecount'] = 20
        return_data['index'] = 2
        return_data['random'] = random.random()

        return return_data

    # 获取会议文集种子
    def getWenJiUrlList(self, resp, hangye):
        return_data = []
        selector = Selector(text=resp)
        try:
            dl_list = selector.xpath("//div[@class='papersList']/dl")
            if dl_list:
                for dl in dl_list:
                    save_data = {}
                    url_template = 'http://navi.cnki.net/knavi/DPaperDetail?pcode={}&lwjcode={}&hycode={}'

                    if dl.xpath("./dt/em/text()"):
                        jibie = dl.xpath("./dt/em/text()").extract_first().strip()
                    else:
                        jibie = ""

                    if dl.xpath("./dt/a/@href"):
                        url_data = dl.xpath("./dt/a/@href").extract_first()

                        # 获取pcode
                        if re.findall(r"pcode=(.*?)&", url_data):
                            pcode = re.findall(r"pcode=(.*?)&", url_data, re.S)[0]
                        elif re.findall(r"pcode=(.*)", url_data):
                            pcode = re.findall(r"pcode=(.*)", url_data, re.S)[0]
                        else:
                            continue

                        # 获取lwjcode
                        if re.findall(r"baseid=(.*?),.*", url_data):
                            lwjcode = re.findall(r"baseid=(.*?),.*", url_data, re.S)[0]
                        elif re.findall(r"baseid=(.*?)&", url_data):
                            lwjcode = re.findall(r"baseid=(.*?)&", url_data, re.S)[0]
                        elif re.findall(r"baseid=(.*)", url_data):
                            lwjcode = re.findall(r"baseid=(.*)", url_data, re.S)[0]
                        else:
                            continue

                        # 获取hycode
                        if re.findall(r"baseid=.*,(.*?)&", url_data):
                            hycode = re.findall(r"baseid=.*,(.*?)&", url_data, re.S)[0]
                        elif re.findall(r"baseid=.*,(.*)", url_data):
                            hycode = re.findall(r"baseid=.*,(.*)", url_data, re.S)[0]
                        else:
                            hycode = ''

                        save_data['url'] = url_template.format(pcode, lwjcode, hycode)
                        save_data['jibie'] = jibie
                        save_data['s_hangYe'] = hangye

                        return_data.append(save_data)

            else:
                return return_data

        except Exception:
            return return_data

        return return_data

    # ==================================== 会议文集-DATA
    # 获取文集详情url
    def getProfileUrl(self, base_url, url):
        try:
            profile_url = base_url + re.findall(r"\?(.*)&hycode", url)[0] + '&pIdx=0'
        except:
            profile_url = ''

        return profile_url

    def geTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title = selector.xpath("//h3/text()").extract_first().strip()

        except Exception:
            title = ''

        return title

    def getTuPian(self, resp):
        selector = Selector(text=resp)
        try:
            src = selector.xpath("//dt[contains(@class, 'pic')]/img/@src").extract_first().strip()
            img = 'http:' + src

        except Exception:
            img = ''

        return img

    def getField(self, resp, para):
        selector = Selector(text=resp)
        try:
            if selector.xpath("//ul/li/p[contains(text(), '" + para + "')]/span/@title"):
                value = selector.xpath("//ul/li/p[contains(text(), '" + para + "')]/span/@title").extract_first().strip()
            else:
                value = selector.xpath("//ul/li/p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()

        except Exception:
            value = ''

        return value

    def guanLianHuoDongHuiYi(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '活动'
        return e

    def guanLianWenJi(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '期刊'
        return e

class HuiYiLunWen_LunWen(Service):
    # 获取列表页首页URL
    def getCatalogUrl(self, url, target_url):
        try:
            pcode = re.findall(r"pcode=(.*?)&", url)[0]
        except:
            pcode = None

        try:
            lwjcode = re.findall(r"lwjcode=(.*?)&", url)[0]
        except:
            lwjcode = None

        if pcode and lwjcode:
            catalog_url = target_url.format(pcode, lwjcode)
        else:
            catalog_url = ''

        return catalog_url

    # 获取列表页翻页URL
    def getPageUpUrl(self, catalog_url, page):
        try:
            url = re.sub(r"\d+$", str(page), catalog_url)
        except:
            url = None

        return url

    # 获取总页数
    def getPageNumber(self, resp):
        selector = Selector(text=resp)
        if selector.xpath("//input[@id='pageCount']/@value"):
            total_page = selector.xpath("//input[@id='pageCount']/@value").extract_first()
        else:
            total_page = 1

        return int(total_page)

    # 获取论文详情页及相关字段
    def getProfileUrl(self, resp, parent_url):
        return_data = []
        selector = Selector(text=resp)

        tr_list = selector.xpath("//tr[@class]")

        for tr in tr_list:
            save_data = {}
            td_list = tr.xpath("./td")

            # 获取论文种子
            try:
                href = td_list[1].xpath('./a/@href').extract_first().strip()
                if re.findall(r"dbCode=(.*?)&", href, re.I):
                    dbcode = re.findall(r"dbCode=(.*?)&", href, re.I)[0]
                elif re.findall(r"dbCode=(.*)", href, re.I):
                    dbcode = re.findall(r"dbCode=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"fileName=(.*?)&", href, re.I):
                    filename = re.findall(r"fileName=(.*?)&", href, re.I)[0]
                elif re.findall(r"fileName=(.*)", href, re.I):
                    filename = re.findall(r"fileName=(.*)", href, re.I)[0]
                else:
                    continue

                if re.findall(r"tableName=(.*?)&", href, re.I):
                    dbname = re.findall(r"tableName=(.*?)&", href, re.I)[0]
                elif re.findall(r"tableName=(.*)", href, re.I):
                    dbname = re.findall(r"tableName=(.*)", href, re.I)[0]
                else:
                    continue

                save_data['url'] = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname

            except:
                continue

            # 获取论文下载URL
            try:
                xiazai = td_list[2].xpath('./ul/li/a/@href').extract_first().strip()
                save_data['xiaZai'] = 'http://navi.cnki.net/knavi/' + xiazai
            except:
                save_data['xiaZai'] = ''

            # 获取在线阅读
            try:
                yuedu = td_list[2].xpath("./ul/li[@class='btn-view']/a/@href").extract_first().strip()
                save_data['zaiXianYueDu'] = 'http://navi.cnki.net/knavi/' + yuedu
            except:
                save_data['zaiXianYueDu'] = ''

            # 获取下载次数
            try:
                save_data['xiaZaiCiShu'] = td_list[6].xpath('./text()').extract_first().strip()
            except:
                save_data['xiaZaiCiShu'] = ''

            save_data['parentUrl'] = parent_url

            return_data.append(save_data)

        return return_data

    # 生成会议列表页请求参数
    def getHuiYiListUrlData(self, pcode, lwjcode, page):
        data = {
            'pcode': pcode,
            'lwjcode': lwjcode,
            'orderBy': 'FN|ASC',
            'pIdx': page
        }

        return data

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
            href = 'http:' + img

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
                    if shijian:
                        com_dict['时间'] = shijian
                    else:
                        com_dict['时间'] = ''
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
                        url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
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

class QiKanLunWen_QiKan(Service):
    def getFenLeiUrl(self, url):
        fenlei_number = [1, 7]
        for number in fenlei_number:
            # 生成分类列表页url
            fenlei_url = url + 'productcode=CJFD&ClickIndex={}&random={}'.format(number, random.random())
            yield fenlei_url

    def getFenLeiData(self, resp, page):
        selector = Selector(text=resp)
        fenlei = selector.xpath("//span[@class='wrap']/text()").extract_first().strip()
        li_list = selector.xpath("//li")
        for li in li_list:
            if li.xpath("./span/a/@title"):
                name1 = li.xpath("./span/a/@title").extract_first()
                a_list = li.xpath('./dl/dd/a')
                for a in a_list:
                    try:
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

                    except Exception:
                        continue

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
            try:
                href = li.xpath("./a/@href").extract_first()
                pcode = re.findall(r"pcode=(.*?)&", href)[0]
                pykm = re.findall(r"&baseid=(.*)", href)[0]
                url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)

                yield {'url': url}

            except Exception:
                continue

    # ============================================= DATA
    def getTitle(self, resp):
        selector = Selector(text=resp)
        try:
            title = selector.xpath("//h3/text()").extract_first().strip()
            # title = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp;)', '', data)).strip()
        except Exception:
            title = ''

        return title

    def getHeXinShouLu(self, resp):
        selector = Selector(text=resp)
        try:
            span_list = selector.xpath("//p[@class='journalType']/span/text()").extract()
            shoulu = '|'.join(span_list).strip()
        except Exception:
            shoulu = ''

        return shoulu

    def getYingWenMingCheng(self, resp):
        selector = Selector(text=resp)
        try:
            p_text = selector.xpath("//dd[@class='infobox']/p[not(@class)]/text()").extract_first()
            data = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp;)', '', p_text)).strip()

        except:
            data = ''

        return data

    def getBiaoShi(self, resp):
        selector = Selector(text=resp)
        try:
            pic_url = 'http:' + selector.xpath("//dt[@id='J_journalPic']/img/@src").extract_first().strip()

        except Exception:
            pic_url = ""

        return pic_url

    def getData(self, resp, para):
        selector = Selector(text=resp)
        try:
            data = selector.xpath("//ul/li[not(@class)]/p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()
        except Exception:
            data =''

        return data

    def getMoreData(self, resp, para):
        selector = Selector(text=resp)
        try:
            datas = selector.xpath("//ul/li[not(@class)]/p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()
            data = re.sub(r"(;|；)", "|", datas)
        except Exception:
            data =''

        return data

    def getYingXiangYinZi(self, resp, para):
        data_dict = {}
        selector = Selector(text=resp)
        try:
            p = selector.xpath("//ul/li[not(@class)]/p[contains(text(), '" + para + "')]")
            if p:
                try:
                    year = re.findall(r"\(?(\d+)\)?", p.xpath("./text()").extract_first())[0]
                except Exception:
                    year = ''
                try:
                    value = p.xpath("./span/text()").extract_first().strip()
                except Exception:
                    value = ''
                data_dict['因子年版'] = year
                data_dict['因子数值'] = value
            else:
                return data_dict

        except Exception:
            return data_dict

        return data_dict


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
        selector = Selector(text=html)
        try:
            tags = selector.xpath("//p[@class='database']").extract()
            database = ''.join(tags)

        except Exception:
            database = ""

        return database

    def getQiKanRongYu(self, html):
        selector = Selector(text=html)
        try:
            tags = selector.xpath("//p[contains(text(), '期刊荣誉')]/following-sibling::p").extract()
            database = ''.join(tags)

        except Exception:
            database = ""

        return database

    def guanLianQiKan(self, url, sha):
        e = {}
        e['url'] = url
        e['sha'] = sha
        e['ss'] = '期刊'
        return e

class QiKanLunWen_LunWen(Service):
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
        html = resp.text
        selector = Selector(text=html)
        dl_list = selector.xpath("//div[@class='yearissuepage']/dl")
        for dl in dl_list:
            try:
                year = dl.xpath("./dt/em/text()").extract_first().strip()
                # 只获取2018-2020年份的期刊论文
                if int(year) >= 2017:
                    stage_list = dl.xpath("./dd/a/text()").extract() # 期列表
                    for stage in stage_list:
                        issue = re.findall(r'No\.(.*)', stage)[0]
                        yield year, issue

                else:
                    continue

            except Exception:
                continue

    # 获取论文列表页种子
    def getArticleListUrl(self, url, data, pcode, pykm):
        '''
        :param data: 【年】【期】数据
        :return: 种子列表
        '''
        # 论文列表页种子 http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year=2018&issue=Z1&pykm=SHGJ&pageIdx=0&pcode=CJFD
        # return_data = []
        year = data[0]
        issue = data[1]
        list_url = url.format(year, issue, pykm, pcode)

        # year = str(list(data.keys())[0])
        # stage_list = data[year]
        # for stages in stage_list:
        #     stage = re.findall(r'No\.(\d+)', stages)[0]
        #     list_url = url.format(year, stage, pykm, pcode)
        #     return_data.append(list_url)

        return list_url

    # 获取文章种子列表
    def getArticleUrlList(self, resp, qiKanUrl, xuekeleibie):
        '''
        获取文章种子列表
        :param html: html源码
        :return: 文章种子列表
        '''
        html = resp.text
        return_data = []
        selector = Selector(text=html)
        try:
            dd_list = selector.xpath("//dd")
            if dd_list:
                for dd in dd_list:
                    save_data = {}
                    # 获取论文种子
                    try:
                        href = dd.xpath("./span[@class='name']/a/@href").extract_first().strip()
                        # Common/RedirectPage?sfield=FN&dbCode=CJFD&filename=SHGJ2018Z2022&tableName=CJFDPREP&url=
                        if re.findall(r"dbCode=(.*?)&", href, re.I):
                            dbcode = re.findall(r"dbCode=(.*?)&", href, re.I)[0]
                        elif re.findall(r"dbCode=(.*)", href, re.I):
                            dbcode = re.findall(r"dbCode=(.*)", href, re.I)[0]
                        else:
                            continue

                        if re.findall(r"fileName=(.*?)&", href, re.I):
                            filename = re.findall(r"fileName=(.*?)&", href, re.I)[0]
                        elif re.findall(r"fileName=(.*)", href, re.I):
                            filename = re.findall(r"fileName=(.*)", href, re.I)[0]
                        else:
                            continue

                        if re.findall(r"tableName=(.*?)&", href, re.I):
                            dbname = re.findall(r"tableName=(.*?)&", href, re.I)[0]
                        elif re.findall(r"tableName=(.*)", href, re.I):
                            dbname = re.findall(r"tableName=(.*)", href, re.I)[0]
                        else:
                            continue

                        save_data['url'] = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname

                    except:
                        continue

                    # 获取论文下载URL
                    try:
                        xiazai = dd.xpath('./ul/li[1]/a/@href').extract_first().strip()
                        save_data['xiaZai'] = 'http://navi.cnki.net/knavi/' + xiazai
                    except:
                        save_data['xiaZai'] = ''

                    # 获取在线阅读
                    try:
                        yuedu = dd.xpath("./ul/li[@class='btn-view']/a/@href").extract_first().strip()
                        save_data['zaiXianYueDu'] = 'http://navi.cnki.net/knavi/' + yuedu
                    except:
                        save_data['zaiXianYueDu'] = ''

                    save_data['xueKeLeiBie'] = xuekeleibie
                    save_data['parentUrl'] = qiKanUrl

                    return_data.append(save_data)

            else:
                return return_data

        except:
            return return_data

        return return_data