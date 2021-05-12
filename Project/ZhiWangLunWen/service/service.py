# -*- coding:utf-8 -*-

"""

"""
import re
import random
import ast
import json
import copy
import hashlib
from urllib import parse

from bs4 import BeautifulSoup
from lxml import etree
from scrapy.selector import Selector


class DomResultHolder(object):
    def __init__(self):
        self.dict = {}
        self.text = None

    def get(self, mode, text):
        if text != self.text:
            self.dict.clear()
            self.text = text

        if mode in self.dict:
            return self.dict[mode]

        if mode == 'Selector':
            self.dict[mode] = Selector(text=text)
            return self.dict[mode]

        if mode == 'BeautifulSoup':
            self.dict[mode] = BeautifulSoup(text, 'html.parser')
            return self.dict[mode]

        raise NotImplementedError


# 父类，有公共属性和方法
class Service(object):
    def __init__(self, logging):
        self.logger = logging
        self.dom_holder = DomResultHolder()

    # 数据类型转换
    @staticmethod
    def get_eval(task_data):
        return ast.literal_eval(task_data)


class XueWeiLunWen_xueWeiShouYuDanWei(Service):

    def get_index_url_data(self):
        data = {
            'productcode': 'CDMD',
            'index': 1,
            'random': random.random()
        }

        return data

    # 获取分类参数
    def get_fen_lei_data_list(self, text):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
    def get_dan_wei_list_url_data(self, data, page):
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
    def get_page_number(self, totalCount):
        if int(totalCount) % 21 == 0:
            return int(int(totalCount) / 21)

        else:
            return int(int(totalCount) / 21) + 1

    # 获取单位数量
    def get_dan_wei_number(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            number_data = selector.xpath("//em[@id='lblPageCount']/text()").extract_first()
            return number_data

        except Exception:
            return 0

    # 获取单位url
    def get_dan_wei_url_list(self, text, value):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
    def ge_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h3[@class='titbox']/text()").extract_first().strip()

        except Exception:
            title = ''

        return title

    def get_field(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            fieldValue = selector.xpath("//p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()

        except Exception:
            fieldValue = ''

        return fieldValue

    def get_zhu_ye(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            fieldValue = selector.xpath("//p[contains(text(), '官方网址')]/span/a/text()").extract_first().strip()

        except Exception:
            fieldValue = ''

        return fieldValue

    def get_tu_pian(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            pic = 'http:' + selector.xpath("//dt[contains(@class, 'pic')]/img/@src").extract_first().strip()

        except Exception:
            pic = ''

        return pic

    def get_biao_qian(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            tag_list = selector.xpath("//h3[@class='titbox']/span/text()").extract()
            tag = '|'.join(tag_list)

        except Exception:
            tag = ''

        return tag

    def guan_lian_dan_wei(self, url, sha):
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
    def get_zhuan_ye_list(self, text, value):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
    def getPageNumber(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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
    def getProfileUrl(self, text, zhuanye, parent_url):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)

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

                save_data[
                    'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname
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
    # 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=BDYX202002006&dbname=CJFDLAST2020'
    def get_id(self, url):
        id_list = re.findall(r"dbcode=(.*?)&filename=(.*?)&dbname=(.*?)$", url, re.I)[0]

        return '|'.join(id_list)

    def get_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title_text = selector.xpath("string(//h1)").extract_first()
            title = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", title_text)).strip()
        except Exception:
            title = ''

        return title

    def get_author(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            zuozhe_list = selector.xpath("//h3[@class='author']//*[not(name()='sup')]/text()").extract()
            zuozhe = '|'.join(zuozhe_list)

        except Exception:
            zuozhe = ''

        return zuozhe

    def get_affiliation(self, text):
        data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            danwei_list = selector.xpath("//h3[@class='author']/following-sibling::h3[1]//text()").extract()
            for danwei in danwei_list:
                # 去除每个作者单位开头序号
                value = re.sub(r"^\d+[.。]", "", danwei).strip()
                data_list.append(value)

            affiliation = '|'.join(data_list)

        except Exception:
            affiliation = ''

        return affiliation

    def get_catalog(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            catalog = selector.xpath("//ul[@class='catalog-list']").extract_first()
            if catalog is None:
                catalog = ''

        except Exception:
            catalog = ''

        return catalog

    def get_abstract(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            abstract = selector.xpath("//span[@class='abstract-text']").extract_first()

        except Exception:
            abstract = ''

        return abstract

    def get_keyword(self, text):
        data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if selector.xpath("//p[@class='keywords']/a"):
                values = selector.xpath("string(//p[@class='keywords'])").extract_first()
                # values = ''.join(value_list)
                # for v in value_list:
                    # 去除每个关键词末尾分号
                    # value = re.sub(r"[;；]$", "", v.strip())
                    # data_list.append(value)
                # value = '|'.join(data_list)
            else:
                values = selector.xpath("//p[@class='keywords']/text()").extract_first()
            value = re.sub(r"[;；]", "|", re.sub(r"[;；]$", "", values.strip()))
            value_list = value.split('|')
            # 每个关键词去除左右空格
            for v in value_list:
                data_list.append(v.strip())
            value = '|'.join(data_list)

        except Exception:
            value = ''

        return value

    def get_funders(self, text):
        funds_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            # 有链接
            a_list = selector.xpath("//p[@class='funds']/a")
            for a in a_list:
                data_dict = {}
                # 获取值
                a_text = a.xpath("./text()").extract_first()
                # 去除每个关键词末尾分号
                data_dict['project_name'] = re.sub(r"[;；]$", "", a_text.strip())
                onclick = a.xpath("./@onclick").extract_first().strip()
                para = self.get_eval(re.findall(r"TurnPageToKnet(\(.*\));$", onclick)[0])
                data_dict[
                    'project_url'] = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                    para[0], parse.quote(para[1]), para[2])
                funds_list.append(data_dict)
            # 无链接
            funds = selector.xpath("//p[@class='funds']/text()").extract()
            for fund in funds:
                data_dict = {}
                # 去除每个关键词末尾分号
                data_dict['project_name'] = re.sub(r"[;；]$", "", fund.strip()).strip()
                funds_list.append(data_dict)

        except Exception:
            return funds_list

        return funds_list

    def get_journal_name(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            name = selector.xpath("//a[contains(@onclick, 'getKns8NaviLink')]/text()").extract_first().strip()

        except Exception:
            name = ''

        return name

    def get_year(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            qihao = selector.xpath("//a[contains(@onclick, 'getKns8YearNaviLink')]/text()").extract_first().strip()
            try:
                year = re.findall(r"(\d{4})[,，]?", qihao)[0]
            except Exception:
                year = ''
            try:
                vol = re.findall(r"[,，]?(\d+)[\(（]", qihao)[0]
            except Exception:
                vol = ''
            try:
                issue = re.findall(r"[（\(](.+)[\)）]", qihao)[0]
            except Exception:
                issue = ''

        except Exception:
            year = ''
            vol = ''
            issue = ''

        return year, vol, issue

    def get_volume(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            qihao = selector.xpath("//a[contains(@onclick, 'getKns8YearNaviLink')]/text()").extract_first().strip()
            vol = re.findall(r"[,，]?(\d+)[\(（]", qihao)[0]

        except Exception:
            vol = ''

        return vol

    def get_issue(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            qihao = selector.xpath("//a[contains(@onclick, 'getKns8YearNaviLink')]/text()").extract_first().strip()
            issue = re.findall(r"(\(\d+\))", qihao)[0]

        except Exception:
            issue = ''

        return issue

    def get_more_fields(self, text, para):
        data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if selector.xpath("//span[contains(text(), '{}')]/following-sibling::p[1]/a".format(para)):
                value_list = selector.xpath("//span[contains(text(), '{}')]/following-sibling::p[1]//text()".format(para)).extract()
                for v in value_list:
                    # 去除每个关键词末尾分号
                    value = re.sub(r"[;；]$", "", v.strip())
                    data_list.append(value)
                field_value = '|'.join(data_list)
            else:
                values = selector.xpath("//span[contains(text(), '{}')]/following-sibling::p[1]/text()".format(para)).extract_first()
                value = re.sub(r"[;；]", "|", re.sub(r"[;；]$", "", values.strip()))
                value_list = value.split('|')
                # 每个关键词去除左右空格
                for v in value_list:
                    data_list.append(v.strip())
                field_value = '|'.join(data_list)

        except Exception:
            field_value = ''

        return field_value

    def get_classification_code(self, text):
        data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if selector.xpath("//span[contains(text(), '分类号')]/following-sibling::p[1]/a"):
                value_list = selector.xpath("//span[contains(text(), '{}')]/following-sibling::p[1]//text()").extract()
                for v in value_list:
                    code_dict = {}
                    # 去除每个关键词末尾分号
                    value = re.sub(r"[;；]$", "", v.strip())
                    code_dict['name'] = ''
                    code_dict['code'] = value.strip()
                    code_dict['type'] = '中图分类'
                    data_list.append(code_dict)
            else:
                values = selector.xpath("//span[contains(text(), '分类号')]/following-sibling::p[1]/text()").extract_first()
                value = re.sub(r"[;；]", "|", re.sub(r"[;；]$", "", values.strip()))
                value_list = value.split('|')
                # 每个关键词去除左右空格
                for v in value_list:
                    code_dict = {}
                    code_dict['name'] = ''
                    code_dict['code'] = v.strip()
                    code_dict['type'] = '中图分类'
                    data_list.append(code_dict)

        except Exception:
            return data_list

        return data_list

    # 获取文内图片
    def get_pic_url(self, href, down):
        return_data = []
        try:
            if re.findall(r"fileName=(.*?)&", href, re.I):
                filename = re.findall(r"fileName=(.*?)&", href, re.I)[0]
            elif re.findall(r"fileName=(.*)", href, re.I):
                filename = re.findall(r"fileName=(.*)", href, re.I)[0]
            else:
                return return_data

            if filename:
                # 图片参数url
                image_data_url = 'https://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(filename)
                # 获取图片参数
                image_data_resp = down(url=image_data_url, method='GET')
                if image_data_resp['status'] == 404:
                    return return_data

                if not image_data_resp['data']:
                    self.logger.error('图片参数获取失败, url: {}'.format(image_data_url))
                    return return_data

                image_data_response = image_data_resp['data'].text
                try:
                    img_para = re.findall(r"var oJson={'IDs':'(.*)'}", image_data_response)[0]
                    if img_para:
                        index_list = img_para.split('||')
                        for index in index_list:
                            image_data = {}
                            url_data = index.split('##')[0]
                            image_title = index.split('##')[1]
                            image_url = 'https://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                            image_data['url'] = image_url
                            image_data['title'] = image_title
                            return_data.append(image_data)

                        return return_data
                    else:
                        return return_data

                except Exception:
                    return return_data
            else:
                return return_data

        except Exception:
            return return_data

    # 关联组图
    def rela_pics(self, url, key, sha):
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '组图'
        except Exception:
            return e

        return e

    # 关联文档
    def rela_doc(self, url, key, sha):
        # 创建关联对象
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
        # 创建关联对象
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e

    # 获取文档
    def get_media(self, media_data, media_key, ss, format='', size=''):
        label_obj = {}
        media_list = []
        try:
            if media_data:
                for media in media_data:
                    if media['url']:
                        media_obj = {
                            'url': media['url'],
                            'title': media.get('title', ''),
                            'desc': '',
                            'sha': hashlib.sha1(media['url'].encode('utf-8')).hexdigest(),
                            'ss': ss,
                            'format': format,
                            'size': size
                        }
                        media_list.append(media_obj)
                label_obj[media_key] = media_list
        except Exception:
            return label_obj

        return label_obj

    # 获取组图
    def get_pics(self, img_data):
        label_obj = {}
        pic_list = []
        try:
            if img_data:
                for img in img_data:
                    if img['url']:
                        pic_obj = {
                            'url': img['url'],
                            'title': img['title'],
                            'desc': "",
                            'sha': hashlib.sha1(img['url'].encode('utf-8')).hexdigest(),
                            'ss': 'image'
                        }
                        pic_list.append(pic_obj)
                label_obj['picture'] = pic_list
        except Exception:
            label_obj['picture'] = []

        return label_obj

    def get_info(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            tag = selector.xpath("//p[@class='total-inform']/span[contains(text(), '{}')]/text()".format(para)).extract_first().strip()
            info = re.sub(r".*[:：]", "", tag).strip()

        except Exception:
            info = ''

        return info

    def get_suo_zai_ye_ma(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            yema = selector.xpath("//label[contains(text(), '页码')]/../b/text()").extract_first().strip()

        except Exception:
            yema = ''

        return yema

    def get_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            value = selector.xpath("//label[contains(text(), '页数')]/../b/text()").extract_first().strip()
            yeshu = {'v': value, 'u': '页'}
        except Exception:
            yeshu = ''

        return yeshu

    def get_size(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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
                url = 'https://kns.cnki.net/kcms/detail/frame/asynlist.aspx?dbcode={}&dbname={}&filename={}&curdbcode={}&reftype={}'.format(
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
    def getLunWenJi(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            wenji_list = selector.xpath("//div[@class='sourinfo']/p//text()").extract()
            wenji = re.sub(r"(\r|\n|\t)", "", ' '.join(wenji_list)).strip()

        except Exception:
            wenji = ''

        return wenji

    def getUrl(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            url = selector.xpath("//a[contains(text(), '" + para + "')]/@href").extract_first().strip()
            if re.match(r"http", url):
                href = url
            else:
                href = 'https://kns.cnki.net' + url

        except Exception:
            href = ''

        return href

    def get_lite_num(self, url, down, host):
        if re.findall(r"dbcode=(.*?)&", url, re.I):
            dbcode = re.findall(r"dbcode=(.*?)&", url, re.I)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url, re.I)[0]
        else:
            return ''

        if re.findall(r"filename=(.*?)&", url, re.I):
            filename = re.findall(r"filename=(.*?)&", url, re.I)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url, re.I)[0]
        else:
            return ''

        index_url = 'https://{}/kcms/detail/block/refcount.aspx?dbcode={}&filename={}'
        num_url = index_url.format(host, dbcode, filename)

        # 获取参考文献页源码
        num_resp = down(url=num_url, method='GET', host=host)
        if not num_resp['data']:
            self.logger.error('参考文献接口页响应失败, url: {}'.format(num_url))
            return

        try:
            num_json = self.get_eval(num_resp['data'].text)
        except:
            return

        return num_json

    def get_annual_trend(self, url, down, host):
        data_list = []
        if re.findall(r"dbcode=(.*?)&", url, re.I):
            dbcode = re.findall(r"dbcode=(.*?)&", url, re.I)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url, re.I)[0]
        else:
            return data_list

        if re.findall(r"filename=(.*?)&", url, re.I):
            filename = re.findall(r"filename=(.*?)&", url, re.I)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url, re.I)[0]
        else:
            return data_list

        # 'https://kns.cnki.net/kcms/detail/block/refyear.aspx?dbcode=CJFD&filename=jzck201809006'
        index_url = 'https://{}/kcms/detail/block/refyear.aspx?dbcode={}&filename={}'
        trend_url = index_url.format(host, dbcode, filename)

        # 获取参考文献页源码
        trend_resp = down(url=trend_url, method='GET', host=host)
        if trend_resp['status'] == 404:
            return data_list

        if not trend_resp['data']:
            self.logger.error('参考文献接口页响应失败, url: {}'.format(trend_url))
            return data_list

        trend_text = trend_resp['data'].text
        # 获取年度分布
        selector = etree.fromstring(trend_text)
        try:
            item_list = selector.xpath("//Item")
            for item in item_list:
                data_dict = {}
                data_dict['year'] = item.xpath("./YEAR")[0].text
                data_dict['reference'] = item.xpath("./REFERENCE")[0].text
                data_dict['sub_reference'] = item.xpath("./SUB_REFERENCE")[0].text
                data_dict['citing'] = item.xpath("./CITING")[0].text
                data_dict['sub_citing'] = item.xpath("./SUB_CITING")[0].text
                data_list.append(data_dict)

        except Exception:
            return data_list

        temp_list = sorted(data_list, key=lambda k: int(k.get('year') if k.get('year') != '#' else 0), reverse=True)
        return temp_list

    # 判断参考文献类型页面是否正确
    def _verify_type(self, divlist, div_number, keyword):
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

    def judge_number(self, num, datas):
        n = 0
        for detail in datas.get('detail', ''):
            n += len(detail.get('content', 0))

        if n == int(num):
            return True
        else:
            return False

    # 获取关联参考文献
    def get_literature(self, text, reftype, url, down, host, num):
        return_data = {}
        return_data['number'] = num
        return_data['detail'] = []
        type_list = ['J', 'A', 'D', 'S', 'P', 'M', 'N', 'Z']

        # =================正式============================
        try:
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

            # 获取参考、引证文献vl参数
            selector = self.dom_holder.get(mode='Selector', text=text)
            try:
                vl = selector.xpath("//input[@id='listv']/@value").extract_first().strip()
            except Exception:
                return return_data

            # 'http://kns.cnki.net/kcms/detail/frame/list.aspx?dbcode=CMFD&filename=2009014335.nh&dbname=CMFD2009&RefType=1&vl='
            # ================================================
            index_url = ('https://{}/kcms/detail/frame/list.aspx?'
                         'dbcode={}'
                         '&filename={}'
                         '&dbname={}'
                         '&RefType={}'
                         '&vl={}')

            lite_url = index_url.format(host, dbcode, filename, dbname, reftype, vl)
            # 获取参考文献页源码
            lite_resp = down(url=lite_url, method='GET', host=host, referer=url)
            if not lite_resp['data']:
                self.logger.error('文献列表接口页响应失败, url: {}'.format(lite_url))
                return

            response = lite_resp['data'].text
            selector = Selector(text=response)

            # 遍历文献类型
            div_list = selector.xpath("//div[@class='essayBox']")
            i = -1
            for div in div_list:
                type_dict = {}
                i += 1
                # 获取实体类型
                entity_type = div.xpath("./div[@class='dbTitle']/text()").extract_first()
                # print(entity_type)
                # 获取CurDBCode参数
                CurDBCode = re.findall(r"pc_(.*)", div.xpath("./div[@class='dbTitle']/b/span/@id").extract_first())[0]
                # 获取该类型总页数
                article_number = int(div.xpath("./div[@class='dbTitle']/b/span/text()").extract_first().strip())
                if article_number % 10 == 0:
                    page_number = int(article_number / 10)
                else:
                    page_number = int((article_number / 10)) + 1

                # 期刊论文
                if '期刊' in entity_type:
                    type_dict['type'] = '期刊论文'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '期刊'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('&nbsp')
                                    try:
                                        data_dict['title'] = re.findall(r"\](.*)\[\w\]", final_list[0])[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0])[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = re.findall(r"\[\w\]\s*\.+?(.*)\.", final_list[0])[0].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['journal_name'] = re.findall(r"(.*)\.\s*\d+", final_list[-1])[0].strip()
                                    except:
                                        data_dict['journal_name'] = ''
                                    try:
                                        data_dict['year_vol_issue'] = re.findall(r"\.\s*(\d+.*)", final_list[-1])[0].strip()
                                    except:
                                        data_dict['year_vol_issue'] = ''
                                    data_dict['full_content'] = one_text
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict['url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '论文'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '会议' in entity_type:
                    type_dict['type'] = '会议论文'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '会议'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = final_list[1].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['collection'] = re.findall(r"(.*)\[\w+\]$", final_list[2].strip())[0].strip()
                                    except:
                                        data_dict['collection'] = ''
                                    try:
                                        data_dict['date'] = final_list[3].strip()
                                    except:
                                        data_dict['date'] = ''
                                    data_dict['full_content'] = one_text
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '论文'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '博士' in entity_type:
                    type_dict['type'] = '学位论文'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '博士'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = final_list[1].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['author_affiliation'] = re.findall(r"(.*)\s+\d+", final_list[2])[0].strip()
                                    except:
                                        data_dict['author_affiliation'] = ''
                                    try:
                                        data_dict['date'] = re.findall(r".*?\s+(\d+)", final_list[2])[0].strip()
                                    except:
                                        data_dict['date'] = ''
                                    data_dict['full_content'] = one_text
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '论文'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '硕士' in entity_type:
                    type_dict['type'] = '学位论文'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '硕士'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[
                                            0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[
                                            0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = final_list[1].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['author_affiliation'] = re.findall(r"(.*)\s+\d+", final_list[2])[
                                            0].strip()
                                    except:
                                        data_dict['author_affiliation'] = ''
                                    try:
                                        data_dict['date'] = re.findall(r".*?\s+(\d+)", final_list[2])[0].strip()
                                    except:
                                        data_dict['date'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '论文'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                # 题录
                elif '题录' in entity_type:
                    type_dict['type'] = '题录'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '题录'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"\](.*?)\.+?", one_text)[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", one_text)[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['other'] = re.findall(r"\.+?(.*)", one_text)[0].strip()
                                    except:
                                        data_dict['other'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '题录'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '图书' in entity_type:
                    type_dict['type'] = '图书'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '图书'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"\](.*?)\[\w\]\s*\.+?", one_text)[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", one_text)[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['other'] = re.findall(r"\.+?(.*)", one_text)[0].strip()
                                    except:
                                        data_dict['other'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict['url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '图书'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '标准' in entity_type:
                    type_dict['type'] = '标准'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '标准'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('. ')
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['standard_number'] = re.sub(r"^\[\d+\]", "", final_list[0].strip()).strip()
                                    except:
                                        data_dict['standard_number'] = ''
                                    try:
                                        data_dict['title'] = re.sub(r"\[\w+\]$", "", final_list[1].strip()).strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[1].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['date'] = final_list[2].strip()
                                    except:
                                        data_dict['date'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '标准'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '专利' in entity_type:
                    type_dict['type'] = '专利'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '专利'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = final_list[1].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['patent_type'] = re.findall(r"(.*)[:：]", final_list[2])[0].strip()
                                    except:
                                        data_dict['patent_type'] = ''
                                    try:
                                        data_dict['publication_number'] = re.findall(r"[:：](.*)", final_list[2])[0].strip()
                                    except:
                                        data_dict['publication_number'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '专利'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '报纸' in entity_type:
                    type_dict['type'] = '报纸'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '报纸'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['author'] = final_list[1].strip()
                                    except:
                                        data_dict['author'] = ''
                                    try:
                                        data_dict['newspaper'] = final_list[2].strip()
                                    except:
                                        data_dict['newspaper'] = ''
                                    try:
                                        data_dict['date'] = re.findall(r"(\d+)\s*[\(（]", final_list[3])[0].strip()
                                    except:
                                        data_dict['date'] = ''
                                    try:
                                        data_dict['edition'] = re.findall(r"\d+[\(（](.*)[）\)]", final_list[3])[0].strip()
                                    except:
                                        data_dict['edition'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '报纸'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                elif '年鉴' in entity_type:
                    type_dict['type'] = '年鉴'
                    type_dict['content'] = []
                    # 获取当前文献类型url
                    current_url = lite_url + '&CurDBCode={}'.format(CurDBCode)
                    # 关联文献种类关键字， 用于判断翻页后当前标签是否是这个题录
                    keyword = '年鉴'
                    # 翻页获取
                    for page in range(page_number):
                        current_page_url = current_url + '&page={}'.format(page + 1)
                        # 获取该页html
                        cur_page_resp = down(url=current_page_url, method='GET', host=host, referer=current_url)
                        if not cur_page_resp['data']:
                            continue

                        resp_text = cur_page_resp['data'].text
                        selector = Selector(text=resp_text)
                        type_div_list = selector.xpath("//div[@class='essayBox']")
                        # 判断参考文献类型页面是否正确
                        status = self._verify_type(type_div_list, i, keyword)
                        if status:
                            leiXingDiv = type_div_list[i]
                            li_list = leiXingDiv.xpath(".//li")
                            for li in li_list:
                                data_dict = {}
                                try:
                                    text_list = li.xpath(".//text()").extract()
                                    con_text = ''.join(text_list)
                                    one_text = re.sub(r"\s+", " ", re.sub(r"(\r|\n|\t)", " ", con_text)).strip()
                                    final_list = one_text.split('.')
                                    data_dict['full_content'] = one_text
                                    try:
                                        data_dict['title'] = re.findall(r"^\[\d+\](.*)\[\w+\]$", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['title'] = ''
                                    try:
                                        data_dict['document_code'] = re.findall(r"\[([A-Za-z])\]", final_list[0].strip())[0].strip()
                                    except:
                                        data_dict['document_code'] = ''
                                    try:
                                        data_dict['organization'] = final_list[1].strip()
                                    except:
                                        data_dict['organization'] = ''
                                    try:
                                        data_dict['date'] = final_list[2].strip()
                                    except:
                                        data_dict['date'] = ''
                                except Exception:
                                    break

                                try:
                                    title_url = li.xpath("./a[@target='kcmstarget']/@href").extract_first().strip()
                                except:
                                    title_url = ''

                                if title_url:
                                    if re.findall(r"dbcode=(.*?)&", title_url, re.I):
                                        dbcode = re.findall(r"dbcode=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbcode=(.*)", title_url):
                                        dbcode = re.findall(r"dbcode=(.*)", title_url, re.I)[0]
                                    else:
                                        dbcode = ''

                                    if re.findall(r"filename=(.*?)&", title_url, re.I):
                                        filename = re.findall(r"filename=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"filename=(.*)", title_url):
                                        filename = re.findall(r"filename=(.*)", title_url, re.I)[0]
                                    else:
                                        filename = ''

                                    if re.findall(r"dbname=(.*?)&", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*?)&", title_url, re.I)[0]
                                    elif re.findall(r"dbname=(.*)", title_url, re.I):
                                        dbname = re.findall(r"dbname=(.*)", title_url, re.I)[0]
                                    else:
                                        dbname = ''

                                    data_dict[
                                        'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode={}&filename={}&dbname={}'.format(
                                        dbcode, filename, dbname)
                                    key = '中国知网|{}|{}|{}'.format(dbcode, filename, dbname)
                                    data_dict['sha'] = hashlib.sha1(key.encode('utf-8')).hexdigest()
                                    data_dict['ss'] = '图书'
                                else:
                                    data_dict['url'] = ''

                                if data_dict not in type_dict['content']:
                                    type_dict['content'].append(data_dict)

                else:
                    self.logger.error('service | 文献列表中有不识别的文献类型')
                    return

                return_data['detail'].append(type_dict)

        except Exception:
            return return_data

        return return_data

    def rela_creators(self, resp):
        return_data = []
        selector = Selector(text=resp)
        try:
            a_list = selector.xpath("//h3[@class='author']//a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    href = a.xpath("./@href").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet.*?(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                            onclick[0],
                            onclick[1],
                            onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['key'] = '中国知网|{}|{}|{}'.format(onclick[0], onclick[1], onclick[2])
                        e['sha'] = hashlib.sha1(e['key'].encode('utf-8')).hexdigest()
                        e['ss'] = '人物'
                        return_data.append(e)
                    elif href:
                        url = 'https://kns.cnki.net' + href.strip()
                        name = a.xpath("./text()").extract_first().strip()
                        e['name'] = name
                        e['url'] = url
                        para_list = re.findall(r"sfield=(.*?)&skey=(.*?)&code=(.*)$", url, re.I)[0]
                        para = '|'.join(para_list)
                        e['key'] = '中国知网|{}'.format(para)
                        e['sha'] = hashlib.sha1(e['key'].encode('utf-8')).hexdigest()
                        e['ss'] = '人物'
                        return_data.append(e)
                    else:
                        continue

        except Exception:
            return return_data

        return return_data

    def rela_organization(self, text):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            a_list = selector.xpath("//h3[@class='author']/following-sibling::h3[1]//a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    href = a.xpath("./@href").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet.*?(\(.*\))", onclick)[0])
                        url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield={}&skey={}&code={}'.format(
                            onclick[0],
                            onclick[1],
                            onclick[2])
                        name = onclick[1]
                        e['name'] = name
                        e['url'] = url
                        e['key'] = '中国知网|{}|{}|{}'.format(onclick[0], onclick[1], onclick[2])
                        e['sha'] = hashlib.sha1(e['key'].encode('utf-8')).hexdigest()
                        e['ss'] = '机构'
                        return_data.append(e)
                    elif href:
                        url = 'https://kns.cnki.net' + href.strip()
                        name = a.xpath("./text()").extract_first().strip()
                        e['name'] = name
                        e['url'] = url
                        para_list = re.findall(r"sfield=(.*?)&skey=(.*?)&code=(.*)$", url, re.I)[0]
                        para = '|'.join(para_list)
                        e['key'] = '中国知网|{}'.format(para)
                        e['sha'] = hashlib.sha1(e['key'].encode('utf-8')).hexdigest()
                        e['ss'] = '机构'
                        return_data.append(e)
                    else:
                        continue

        except Exception:
            return return_data

        return return_data

    def guanLianDaoShi(self, text):
        data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            a_list = selector.xpath("//div[span[contains(text(), '导师')]]/p/a")
            if a_list:
                for a in a_list:
                    e = {}
                    onclick = a.xpath("./@onclick").extract_first()
                    if onclick:
                        onclick = ast.literal_eval(re.findall(r"TurnPageToKnet.*?(\(.*\))", onclick)[0])
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

    def guanLianWenJi(self, url):
        e = {}
        if url:
            e['url'] = url
            e['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            e['ss'] = '期刊'

            return e

        else:
            return e

    def rela_journal(self, url):
        e = {}
        if url:
            e['url'] = url
            e['key'] = '中国知网|' + re.findall(r"pykm=(\w+)$", url)[0]
            e['sha'] = hashlib.sha1(e['key'].encode('utf-8')).hexdigest()
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

    def get_people(self, zuozhe, daoshi, t):
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
                people['url'] = people['url']
                people['name'] = people['name']
                people['year'] = t

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
    def getFenLeiDataList(self, text):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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
    def getWenJiUrlList(self, text, hangye):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            dl_list = selector.xpath("//div[@class='papersList']/dl")
            if dl_list:
                for dl in dl_list:
                    save_data = {}
                    url_template = 'https://navi.cnki.net/knavi/DPaperDetail?pcode={}&lwjcode={}&hycode={}'

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

    def geTitle(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h3/text()").extract_first().strip()

        except Exception:
            title = ''

        return title

    def getTuPian(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            src = selector.xpath("//dt[contains(@class, 'pic')]/img/@src").extract_first().strip()
            img = 'http:' + src

        except Exception:
            img = ''

        return img

    def getField(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            if selector.xpath("//ul/li/p[contains(text(), '" + para + "')]/span/@title"):
                value = selector.xpath(
                    "//ul/li/p[contains(text(), '" + para + "')]/span/@title").extract_first().strip()
            else:
                value = selector.xpath(
                    "//ul/li/p[contains(text(), '" + para + "')]/span/text()").extract_first().strip()

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
    def getPageNumber(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        if selector.xpath("//input[@id='pageCount']/@value"):
            total_page = selector.xpath("//input[@id='pageCount']/@value").extract_first()
        else:
            total_page = 1

        return int(total_page)

    # 获取论文详情页及相关字段
    def getProfileUrl(self, text, parent_url):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)

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

                save_data[
                    'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname

            except:
                continue

            # 获取论文下载URL
            try:
                xiazai = td_list[2].xpath('./ul/li/a/@href').extract_first().strip()
                save_data['xiaZai'] = 'https://navi.cnki.net/knavi/' + xiazai
            except:
                save_data['xiaZai'] = ''

            # 获取在线阅读
            try:
                yuedu = td_list[2].xpath("./ul/li[@class='btn-view']/a/@href").extract_first().strip()
                save_data['zaiXianYueDu'] = 'https://navi.cnki.net/knavi/' + yuedu
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
    def getField(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            fValue = selector.xpath("//label[contains(text(), '" + para + "')]/../text()").extract_first().strip()
        except:
            fValue = ''

        return fValue

    # 获取官网地址
    def getGuanWangDiZhi(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            url = selector.xpath("//label[contains(text(), '官方网址')]/../a/text()").extract_first().strip()
        except:
            url = ''

        return url

    # 获取机构名
    def getJiGouName(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            name = selector.xpath("//h2[@class='name']/text()").extract_first()
        except:
            name = ''

        return name

    # 获取图片
    def getTuPian(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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

    def getSuoZaiDanWei(self, text, shijian):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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

    def getGuanLianQiYeJiGou(self, text):
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
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


class QiKanLunWen_QiKan(Service):
    def get_fen_lei_url(self, url):
        fenlei_number = [1, 8]
        for number in fenlei_number:
            # 生成分类列表页url
            fenlei_url = url + 'productcode=CJFD&ClickIndex={}&random={}'.format(number, random.random())
            yield fenlei_url

    def get_fen_lei_data(self, text, page):
        selector = self.dom_holder.get(mode='Selector', text=text)
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

    def get_page_number(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
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

    def get_qi_kan_lie_biao_page_data(self, SearchStateJson, page):
        data = {
            'SearchStateJson': SearchStateJson,
            'displaymode': 1,
            'pageindex': int(page),
            'pagecount': 21,
            # 'index': re.findall(r"ClickIndex=(.*?)&", url)[0],
            'random': random.random()
        }

        return data

    def get_qi_kan_list(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        li_list = selector.xpath("//ul[@class='list_tup']/li")
        for li in li_list:
            try:
                href = li.xpath("./a/@href").extract_first()
                pcode = re.findall(r"pcode=(.*?)&", href)[0]
                pykm = re.findall(r"&baseid=(.*)", href)[0]
                url = "https://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)

                yield {'url': url}

            except Exception:
                continue

    # ============================================= DATA
    def get_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h3/text()").extract_first().strip()
            # title = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp;)', '', data)).strip()
        except Exception:
            title = ''

        return title

    def get_he_xin_shou_lu(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            span_list = selector.xpath("//p[@class='journalType']/span/text()").extract()
            shoulu = '|'.join(span_list).strip()
        except Exception:
            shoulu = ''

        return shoulu

    def get_parallel_title(self, text):
        soup = self.dom_holder.get(mode='BeautifulSoup', text=text)
        try:
            p = soup.h3.p.get_text()
            en_title = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp;)', '', p)).strip()
        except Exception:
            en_title = ''

        return en_title

    def get_cover(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            pic_url = 'https:' + selector.xpath("//dt[@id='J_journalPic']/img/@src").extract_first().strip()

        except Exception:
            pic_url = ''

        return pic_url

    def get_data(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            fileds = selector.xpath(
                "//ul/li[not(@class='tit')]/p[contains(text(), '{}')]/span/text()".format(para)).extract_first().strip()
        except Exception:
            fileds = ''

        return fileds

    def get_counts(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            span = selector.xpath(
                "//ul/li[not(@class='tit')]/p[contains(text(), '{}')]/span/text()".format(para)).extract_first().strip()
            counts = re.findall(r"\d+", span)[0]
        except Exception:
            counts = ''

        return counts

    def get_more_data(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            datas = selector.xpath(
                "//ul/li[not(@class='tit')]/p[contains(text(), '{}')]/span/text()".format(para)).extract_first().strip()
            data = re.sub(r"(;|；)", "|", datas)
        except Exception:
            data = ''

        return data

    def get_impact_factor(self, text):
        data_list = []
        data_dict = {}
        impact_factors = ['复合影响因子', '综合影响因子']
        en_if = ['combined_impact_factor', 'comprehensive_impact_factor']
        selector = self.dom_holder.get(mode='Selector', text=text)
        for i in range(len(impact_factors)):
            try:
                p = selector.xpath("//ul/li[not(@class)]/p[contains(text(), '{}')]".format(impact_factors[i]))
                if p:
                    try:
                        year = re.findall(r"\(?(\d+)\)?", p.xpath("./text()").extract_first())[0]
                    except Exception:
                        year = ''
                    try:
                        value = p.xpath("./span/text()").extract_first().strip()
                    except Exception:
                        value = ''
                    data_dict['year'] = year
                    data_dict[en_if[i]] = value

                else:
                    return data_list

            except Exception:
                return data_list

        data_list.append(data_dict)
        return data_list

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

    def get_databases(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            tags = selector.xpath("//p[@class='database']/@title").extract()
            database = '|'.join(tags)
        except Exception:
            database = ''

        return database

    def get_chinese_core_journals(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            tag = selector.xpath("//p[@class='hostUnit']/span/@title").extract_first()
            banben = re.sub(r"[\|;；]$", "", re.sub(r"[,，]", "|", tag))

        except Exception:
            banben = ''

        return banben

    def get_journal_honors(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            tags = selector.xpath("//p[contains(text(), '期刊荣誉')]/following-sibling::p").extract()
            database = ''.join(tags)

        except Exception:
            database = ''

        return database

    def rela_journal(self, url, key, sha):
        e = {}
        e['url'] = url
        e['key'] = key
        e['sha'] = sha
        e['ss'] = '期刊'
        return e


class QiKanLunWen_LunWen(Service):
    # 生成单个知网期刊的时间列表种子
    def qikan_time_list_url(self, url, timelisturl):
        """
        :param url: 期刊种子
        :return: 时间列表种子
        """
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

        qikan_time_list_url = timelisturl.format(pcode, pykm)

        return qikan_time_list_url, pcode, pykm

    # 获取期刊【年】、【期】列表
    def get_qikan_time_list(self, resp):
        """
        :param html: html源码
        :return: 【年】、【期】列表
        """
        issues_list = []
        text = resp.text
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            dl_list = selector.xpath("//div[@class='yearissuepage']/dl")
            if dl_list:
                for dl in dl_list:
                    year = dl.xpath("./dt/em/text()").extract_first().strip()
                    # # 只获取2014-2000年份的期刊论文
                    # if int(year) >= 2000:
                    #     continue

                    stage_list = dl.xpath("./dd/a/text()").extract()  # 期列表
                    for stage in stage_list:
                        issue = re.findall(r'No\.(.*)', stage)[0]
                        issues_list.append((year, issue))
                    # else:
                    #     break

                if not issues_list:
                    return
            else:
                return issues_list

        except Exception:
            return issues_list

        return issues_list

    # 获取论文列表页种子
    def get_article_list_url(self, url, data, pcode, pykm):
        """
        :param data: 【年】【期】数据
        :return: 种子列表
        """
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

    # 获取文章详情种子列表
    def get_article_url_list(self, resp, qiKanUrl, xuekeleibie, year):
        '''
        获取文章种子列表
        :param html: html源码
        :return: 文章种子列表
        '''
        text = resp.text
        return_data = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            dt_list = selector.xpath("//dt")
            if dt_list:
                count = 1
                for dt in dt_list:
                    try:
                        theme = dt.xpath("./text()").extract_first().strip()
                    except Exception:
                        theme = ''
                    dd_list = dt.xpath("./following-sibling::dd[count(preceding-sibling::dt)={}]".format(count))
                    count += 1
                    if dd_list:
                        for dd in dd_list:
                            save_data = {}
                            save_data['theme'] = theme
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

                                save_data[
                                    'url'] = 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname

                            except:
                                continue

                            # 获取论文下载URL
                            try:
                                xiazai = dd.xpath('./ul/li[1]/a/@href').extract_first().strip()
                                save_data['xiaZai'] = 'https://navi.cnki.net/knavi/' + xiazai
                            except:
                                save_data['xiaZai'] = ''

                            # 获取在线阅读
                            try:
                                yuedu = dd.xpath("./ul/li[@class='btn-view']/a/@href").extract_first().strip()
                                save_data['zaiXianYueDu'] = 'https://navi.cnki.net/knavi/' + yuedu
                            except:
                                save_data['zaiXianYueDu'] = ''

                            save_data['xueKeLeiBie'] = xuekeleibie
                            save_data['parentUrl'] = qiKanUrl
                            save_data['year'] = year[0]
                            save_data['issue'] = year[1]

                            return_data.append(save_data)
                    else:
                        continue
            else:
                return return_data

        except:
            return return_data

        return return_data
