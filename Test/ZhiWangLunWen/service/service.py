# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import ast
import random
import hashlib
from lxml import html
from urllib import parse
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


class Server(object):
    # 获取dbcode
    def getDbCode(self, url):
        if re.findall(r"dbcode=(.*?)&", url):
            dbcode = re.findall(r"dbcode=(.*?)&", url)[0]
        elif re.findall(r"dbcode=(.*)", url):
            dbcode = re.findall(r"dbcode=(.*)", url)[0]
        elif re.findall(r"dbCode=(.*?)&", url):
            dbcode = re.findall(r"dbCode=(.*?)&", url)[0]
        elif re.findall(r"dbCode=(.*)", url):
            dbcode = re.findall(r"dbCode=(.*)", url)[0]
        else:
            return

        return dbcode

    # 获取filename
    def getFilename(self, url):
        if re.findall(r"filename=(.*?)&", url):
            filename = re.findall(r"filename=(.*?)&", url)[0]
        elif re.findall(r"filename=(.*)", url):
            filename = re.findall(r"filename=(.*)", url)[0]
        elif re.findall(r"fileName=(.*?)&", url):
            filename = re.findall(r"fileName=(.*?)&", url)[0]
        elif re.findall(r"fileName=(.*)", url):
            filename = re.findall(r"fileName=(.*)", url)[0]
        else:
            return

        return filename

    # 获取dbname
    def getDbname(self, url):
        if re.findall(r"tableName=(.*?)&", url):
            dbname = re.findall(r"tableName=(.*?)&", url)[0]
        elif re.findall(r"tableName=(.*)", url):
            dbname = re.findall(r"tableName=(.*)", url)[0]
        else:
            return

        return dbname

    # 获取参考文献首页url
    def getCanKaoWenXianIndexUrl(self, filename, dbcode, dbname):
        index_url = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                     'filename={}'
                     '&dbcode={}'
                     '&dbname={}'
                     '&reftype=1'
                     '&catalogId=lcatalog_CkFiles'
                     '&catalogName=')

        return index_url.format(filename, dbcode, dbname)

    # 获取题录数据
    def getTiLu(self, li):
        data = {}
        try:
            data["实体类型"] = "题录"
        except:
            data["实体类型"] = ""
        try:

            data["其它信息"] = re.sub(r'\s+', ' ',
                                  re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()").extract_first()))
        except:
            data["其他信息"] = ""
        try:
            data["标题"] = re.sub(r'\s+', ' ',
                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first()))
        except:
            data["标题"] = ""

        return data

    # 获取学术期刊
    def getXueShuQiKan(self, li):
        data = {}
        try:
            data['年卷期'] = ''.join(
                re.findall(r"[^&nbsp\r\n\s]", li.xpath("./a[3]/text()").extract_first()))
        except:
            data['年卷期'] = ""
        try:
            data['实体类型'] = '期刊论文'
        except:
            data['实体类型'] = ""
        try:
            zuoZhe = re.sub(r'\s+', ' ',
                            re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./text()").extract_first()))
            data['作者'] = re.sub(',', '|', ''.join(re.findall(r'\.(.*?)\.', zuoZhe)))
        except:
            data['作者'] = ""
        try:
            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                "./a[@target='kcmstarget']/text()").extract_first()))
        except:
            data['标题'] = ""
        try:
            data['刊名'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                    li.xpath("./a[2]/text()").extract_first()))
        except:
            data['刊名'] = ""

        return data

    # 获取国际期刊
    def getGuoJiQiKan(self, li):
        data = {}
        try:
            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first())
        except:
            data['标题'] = ""
        try:
            data['实体类型'] = '外文文献'
        except:
            data['实体类型'] = ""
        try:
            try:
                year = str(re.findall(r"(\d{4})", li.xpath("./text()").extract_first())[0])
            except:
                year = ""
            try:
                qi = str(re.findall(r"(\(.*\))", li.xpath("./text()").extract_first())[0])
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
                                                                 li.xpath("./text()").extract_first())))[0]
        except:
            data['作者'] = ''
        try:
            data['url'] = 'http://kns.cnki.net' + li.xpath("./a/@href").extract_first()
        except:
            data['url'] = ''

        return data

    # 获取图书
    def getTuShu(self, li):
        data = {}
        try:
            data['实体类型'] = '图书'
        except:
            data['实体类型'] = ""
        try:
            data['其它信息'] = re.sub(r'\s+', ' ', re.sub('.*\[M\]\.', '', ''.join(
                re.findall(r"[^&nbsp\r\n]", li.xpath("./text()").extract_first()))))
        except:
            data['其他信息'] = ""
        try:
            data['标题'] = re.findall(r"(.*)\[M\]", re.sub(r'(\r|\n|&nbsp)', '',
                                                         li.xpath("./text()").extract_first()))[0]
        except:
            data['标题'] = ""

        return data

    # 获取学位
    def getXueWei(self, li):
        data = {}
        try:
            data['标题'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '', li.xpath(
                "./a[@target='kcmstarget']/text()").extract_first()))
        except:
            data['标题'] = ""
        try:
            data['实体类型'] = '学位论文'
        except:
            data['实体类型'] = ""
        try:
            re_time = re.compile("\d{4}")
            data['时间'] = \
                [re.findall(re_time, time)[0] for time in li.xpath(".//text()").extract() if
                 re.findall(re_time, time)][0]
        except:
            data['时间'] = ""
        try:
            data['作者'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                    re.findall(r"\[D\]\.(.*)\.",
                                                               li.xpath("./text()").extract_first())[
                                                        0]))
        except:
            data['作者'] = ""
        try:
            data['机构'] = re.sub(r'\s+', ' ', re.sub(r'(\r|\n|&nbsp)', '',
                                                    li.xpath("./a[2]/text()").extract_first()))
        except:
            data['机构'] = ""

        return data

    # 获取标准
    def getBiaoZhun(self, li):
        data = {}
        try:
            data['标准号'] = ''.join(re.findall(r"[^\r\n]", li.xpath("./text()").extract_first()))
        except:
            data['标准号'] = ''
        try:
            data['标题'] = ''.join(re.findall(r"[^\r\n\.]", li.xpath("./a/text()").extract_first()))
        except:
            data['标题'] = ''
        try:
            data['时间'] = ''.join(
                re.findall(r"[^\r\n\s\.\[S\]]", li.xpath("./text()").extract()[1]))
        except:
            data['时间'] = ''
        try:
            data['实体类型'] = '标准'
        except:
            data['实体类型'] = ""
        try:
            url = li.xpath("./a/@href").extract_first()
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

        return data

    # 获取专利
    def getZhuanLi(self, li):
        data = {}
        try:
            data['标题'] = re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first())
        except:
            data['标题'] = ''
        try:
            zuozhe = re.findall(r'\. (.*?)\.', re.sub(r'\s+', ' ',
                                                      re.sub(r'(\r|\n|&nbsp)', '',
                                                             li.xpath('./text()').extract_first())))[
                0]
            data['作者'] = re.sub(',', '|', zuozhe)
        except:
            data['作者'] = ''
        try:
            data['类型'] = re.findall(r'.*\. (.*?)\:', re.sub(r'\s+', ' ',
                                                            re.sub(r'(\r|\n|&nbsp)', '',
                                                                   li.xpath('./text()').extract_first())))[0]
        except:
            data['类型'] = ''
        try:
            data['公开号'] = re.findall('\:(.*?)\,', re.sub(r'\s+', ' ',
                                                         re.sub(r'(\r|\n|&nbsp)', '',
                                                                li.xpath('./text()').extract_first())))[0]
        except:
            data['公开号'] = ''
        try:
            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href').extract_first()
        except:
            data['url'] = ''
        try:
            data['实体类型'] = '专利'
        except:
            data['实体类型'] = ""

        return data

    # 获取报纸
    def getBaoZhi(self, li):
        data = {}
        try:
            data['标题'] = re.sub(r'\s+', ' ',
                                re.sub(r'(\r|\n|&nbsp)', '', li.xpath("./a/text()").extract_first()))
        except:
            data['标题'] = ''
        try:
            data['机构'] = re.findall(r'.*\.(.*?)\.', re.sub('\s+', ' ',
                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                  li.xpath("./text()").extract_first())))[0]
        except:
            data['机构'] = ''
        try:
            data['时间'] = re.findall(r'. (\d{4}.*)', re.sub('\s+', ' ',
                                                           re.sub(r'(\r|\n|&nbsp)', '',
                                                                  li.xpath("./text()").extract_first())))[0]
        except:
            data['时间'] = ''
        try:
            data['url'] = 'http://kns.cnki.net' + li.xpath('./a/@href').extract_first()
        except:
            data['url'] = ''
        try:
            data['实体类型'] = '报纸'
        except:
            data['实体类型'] = ""

        return data

    # 获取年鉴
    def getNianJian(self, li):
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
                                                                 li.xpath('./text()').extract_first())))[0]
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

        return data

    # 获取会议
    def getHuiYi(self, li):
        data = {}
        try:
            data['标题'] = li.xpath("./a/text()").extract_first()
        except:
            data['标题'] = ''
        try:
            data['作者'] = re.sub(r"(,|，)", "|", re.findall(r"\[A\]\.(.*?)\.",
                                                          re.sub(r"(\r|\n|\s+)", "",
                                                                 li.xpath("./text()").extract_first()))[0])
        except:
            data['作者'] = ''
        try:
            data['文集'] = re.findall(r"\[A\]\..*?\.(.*?)\[C\]",
                                    re.sub(r"(\r|\n|\s+)", "",
                                           li.xpath("./text()").extract_first()))[0]
        except:
            data['文集'] = ''
        try:
            data['时间'] = {
                "Y": re.findall(r"\[C\]\.(.*)", re.sub(r"(\r|\n|\s+)", "", li.xpath("./text()").extract_first()))[0]}
        except:
            data['时间'] = {}

        data['实体类型'] = '会议论文'

        return data

    # 获取组图参数url
    def getImageDataUrl(self, resp):
        return_data = []
        selector = Selector(text=resp)
        data = selector.xpath("//a[@class='btn-note']/@href").extract_first()
        if not data:
            return return_data

        try:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data)[0]
        except:
            fnbyIdAndName = None
        if not fnbyIdAndName:
            return return_data

        # 图片参数url
        image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)

        return image_data_url

    # 获取组图
    def getZuTu(self, resp):
        return_data = []
        resp_re = re.findall(r"var oJson={'IDs':(.*)}", resp)
        if not resp_re:
            return return_data

        resp_number = len(resp_re[0])
        if resp_number > 5:
            index_list = resp_re[0].split('||')
            for index in index_list:
                image_data = {}
                try:
                    url_data = re.sub(r"\'", "", re.findall(r"(.*)##", index)[0])
                except:
                    continue
                try:
                    image_title = re.sub(r"\'", "", re.findall(r"##(.*)", index)[0])
                except:
                    continue

                image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                image_data['url'] = image_url
                image_data['title'] = image_title
                image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                return_data.append(image_data)

            return return_data

        return return_data


class HuiYiLunWen_QiKanTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 获取学科导航的最底层导航列表
    def getNavigationList(self, resp):
        return_data = []
        selector = Selector(text=resp)
        div_list = selector.xpath("//div[@class='guide']")
        for div in div_list:
            wrap_text = div.xpath(".//span[@class='wrap']/text()").extract_first()
            if not wrap_text:
                continue

            if '学科导航' in wrap_text:
                li_list = div.xpath(".//ul[@class='contentbox']/li")
                for li in li_list:
                    # 获取'_'前部分栏目名
                    firstname = li.xpath("./span[@class='refirstcol']/a/@title").extract_first()
                    if not firstname:
                        continue

                    a_list = li.xpath("./dl[@class='resecondlayer']/dd/a")
                    for a in a_list:
                        save_data = {}
                        lastname = a.xpath("./@title").extract_first()
                        if not lastname:
                            continue

                        onclick = a.xpath("./@onclick").extract_first()
                        if not onclick:
                            continue

                        # 生成完整栏目名
                        save_data['lanmu_name'] = firstname + '_' + lastname
                        try:
                            # 获取栏目url参数
                            save_data['lanmu_url_data'] = re.findall(r"(\(.*\))", onclick)[0]
                        except:
                            continue

                        return_data.append(save_data)

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
        selector = Selector(text=resp)
        lblCount_text = selector.xpath("//em[@class='lblCount']/text()").extract_first()
        if not lblCount_text:
            return None

        return_data = re.findall(r"\d+", lblCount_text)
        if not return_data:
            return None

        return return_data[0]

    # 生成文集总页数
    def getWenJiPageNumber(self, huiYiWenJi_Number):
        if int(huiYiWenJi_Number) % 20 == 0:
            return int(int(huiYiWenJi_Number) / 20)

        else:
            return int(int(huiYiWenJi_Number) / 20) + 1

    # 获取会议文集种子
    def getWenJiUrlList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        dl_list = selector.xpath("//div[@class='papersList']/dl")
        for dl in dl_list:
            save_data = {}
            url_template = 'http://navi.cnki.net/knavi/DPaperDetail?pcode={}&lwjcode={}&hycode={}'
            url_data = dl.xpath("./dt/a/@href").extract_first()
            if not url_data:
                continue

            jibie = dl.xpath("./dt/em/text()").extract_first()
            if not jibie:
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

            url = url_template.format(pcode, lwjcode, hycode)
            save_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            save_data['url'] = url
            save_data['jibie'] = jibie

            return_data.append(save_data)

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


class HuiYiLunWen_LunWenDataServer(Server):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取标题
    def getArticleTitle(self, resp):
        selector = Selector(text=resp)
        title = selector.xpath("//h2[@class='title']/text()").extract_first()
        if not title:
            return ""

        return title

    # 获取作者
    def getZuoZhe(self, resp):
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='author']/span/a")
        name_list = []

        for a in a_list:
            name = a.xpath("./text()").extract_first()
            if not name:
                continue

            name_list.append(name)

        return '|'.join(name_list)

    # 获取发布单位
    def getFaBuDanWei(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='orgn']/span/a")
        for a in a_list:
            url_data = a.xpath("./@onclick").extract_first()
            if not url_data:
                continue
            try:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", url_data)[0])
                zuoZheDanWei = url_data[1]
                return_data.append(zuoZheDanWei)
            except:
                continue

        return '|'.join(return_data)

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='orgn']/span/a")
        for a in a_list:
            url_data = a.xpath("./@onclick").extract_first()
            if not url_data:
                continue

            try:
                url_data = eval(re.findall(r"(\(.*\))", url_data)[0])
                sfield = url_data[0]
                skey = parse.quote(url_data[1])
                code = url_data[2]
                url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                       'sfield={}&skey={}&code={}'.format(sfield, skey, code))
                url_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

                return_data.append({'url': url, 'ss': '机构', 'sha': url_sha1})
            except:
                continue

        return return_data

    # 获取摘要
    def getZhaiYao(self, resp):
        selector = Selector(text=resp)
        zhaiYao = selector.xpath("//span[@id='ChDivSummary']/text()").extract_first()
        if not zhaiYao:
            return ""

        return zhaiYao

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '关键词' in title:
                a_list = p.xpath("./a")

                for a in a_list:
                    a_text = a.xpath("./text()").extract_first()
                    if not a_text:
                        continue

                    try:
                        guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;]', a_text))
                        return_data.append(guanJianCi)
                    except:
                        continue

        return '|'.join(return_data)

    # 获取时间
    def getShiJian(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '会议时间' in title:
                fenLeiHao = p.xpath("./text()").extract_first()
                if not fenLeiHao:
                    return ""

                return ''.join(re.sub(';', '|', fenLeiHao))

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '分类号' in title:
                fenLeiHao = p.xpath("./text()").extract_first()
                if not fenLeiHao:
                    return ""

                return ''.join(re.sub(';', '|', fenLeiHao))

    # 获取组图参数url
    def getImageDataUrl(self, resp):
        return_data = []
        selector = Selector(text=resp)
        data = selector.xpath("//a[@class='btn-note']/@href").extract_first()
        if not data:
            return return_data

        try:
            fnbyIdAndName = re.findall(r"filename=(.*)&", data)[0]
        except:
            fnbyIdAndName = None
        if not fnbyIdAndName:
            return return_data

        # 图片参数url
        image_data_url = 'http://image.cnki.net/getimage.ashx?fnbyIdAndName={}'.format(fnbyIdAndName)

        return image_data_url

    # 获取组图
    def getZuTu(self, resp):
        return_data = []
        resp_re = re.findall(r"var oJson={'IDs':(.*)}", resp)
        if not resp_re:
            return return_data

        resp_number = len(resp_re[0])
        if resp_number > 5:
            index_list = resp_re[0].split('||')
            for index in index_list:
                image_data = {}
                try:
                    url_data = re.sub(r"\'", "", re.findall(r"(.*)##", index)[0])
                except:
                    continue
                try:
                    image_title = re.sub(r"\'", "", re.findall(r"##(.*)", index)[0])
                except:
                    continue

                image_url = 'http://image.cnki.net/getimage.ashx?id={}'.format(url_data)
                image_data['url'] = image_url
                image_data['title'] = image_title
                image_data['sha'] = hashlib.sha1(image_url.encode('utf-8')).hexdigest()
                return_data.append(image_data)

            return return_data

        return return_data

    # 获取PDF下载链接
    def getXiaZai(self, resp):
        selector = Selector(text=resp)
        download_url = selector.xpath("//a[@id='pdfDown']/@href").extract_first()
        if not download_url:
            return ""

        url = ''.join(re.findall(r"[^\n\s']", download_url))
        # http://kns.cnki.net
        if re.search(r"http", url):
            return url

        return 'http://kns.cnki.net' + url

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '页码' in title:
                xiaZaiYeMa = span.xpath("./b/text()").extract_first()
                if not xiaZaiYeMa:
                    return ""

                return xiaZaiYeMa

    # 获取页数
    def getYeShu(self, resp):
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(resp))
        if yeShu:

            return {"v": yeShu[0], "u": "页"}
        else:

            return {}

    # 获取大小
    def getDaXiao(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '大小' in title:
                daXiao = span.xpath("./b/text()").extract_first()
                if not daXiao:
                    return {}

                try:
                    v = re.findall(r'\d+', daXiao)[0]
                except:
                    v = ''
                try:
                    u = re.findall(r"[^\d]", daXiao)[0]
                except:
                    u = 'K'

                return {'v': v, 'u': u}

    # 获取论文集url
    def getLunWenJiDataUrl(self, resp):
        if re.findall(r"RegisterSBlock(\(.*?\));", resp):
            try:
                data = ast.literal_eval(re.findall(r"RegisterSBlock(\(.*?\));", resp)[0])
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
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='sourinfo']/p")
        for p in p_list:
            p_text = p.xpath("./text()").extract_first()
            if not p_text:
                continue

            data = re.sub(r"(\r|\n|\s+|\t)", "", p_text)
            return_data += data

        return return_data

    # 获取下载次数
    def getXiaZaiCiShu(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '下载' in title:
                xiaZaiCiShu = span.xpath("./b/text()").extract_first()
                if not xiaZaiCiShu:
                    return ""

                return xiaZaiCiShu

    # 获取在线阅读地址
    def getZaiXianYueDu(self, resp):
        selector = Selector(text=resp)
        read_url = selector.xpath("//a[@class='icon icon-dlcrsp xml']/@href").extract_first()
        if not read_url:
            return ""

        if re.search(r"http", read_url):
            return read_url

        return 'http://kns.cnki.net' + read_url

    # 获取关联活动_会议
    def getGuanLianHuoDong_HuiYi(self, url):
        return_data = {}
        try:
            save_url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?' + re.findall(r"\?(.*)", url)[
                0]
            return_data['sha'] = hashlib.sha1(save_url.encode('utf-8')).hexdigest()
            return_data['url'] = save_url
            return return_data

        except:
            return return_data

    # 获取关联文集
    def getGuanLianWenJi(self, url):
        return_data = {}
        return_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
        return_data['url'] = url

        return return_data

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='author']/span/a")
        for a in a_list:
            a_onclick = a.xpath("./@onclick").extract_first()
            if not a_onclick:
                continue

            try:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a_onclick)[0])
            except:
                continue

            sfield = url_data[0]
            skey = parse.quote(url_data[1])
            code = url_data[2]
            if not sfield or not skey:
                continue

            name = a.xpath("./text()").extract_first()
            if not name:
                continue

            url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                   'sfield={}'
                   '&skey={}'
                   '&code={}'.format(sfield, skey, code))
            sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

            return_data.append({'sha': sha1, 'url': url, 'name': name, 'ss': '人物'})

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
        li_list = selector.xpath("//li")
        for li in li_list:
            name1 = li.xpath("./span/a/@title").extract_first()
            if not name1:
                continue

            a_list = li.xpath('./dl/dd/a')
            for a in a_list:
                name2 = a.xpath("./@title").extract_first()
                a_onclick = a.xpath("./@onclick").extract_first()
                if not name2 or not a_onclick:
                    continue
                try:
                    onclick = ast.literal_eval(re.findall(r"(\(.*\))", a_onclick)[0])
                except:
                    continue

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
                    'random': random.random()
                }

                yield {'column_name': name1 + '_' + name2, 'data': data, 'SearchStateJson': SearchStateJson}

    def getPageNumber(self, resp):
        selector = Selector(text=resp)
        try:
            data_sum = int(selector.xpath("//em[@class='lblCount']/text()").extract_first())
        except:
            return 0

        if int(data_sum) % 21 == 0:
            page_number = int(int(data_sum) / 21)
            return page_number

        else:
            page_number = int(int(data_sum) / 21) + 1
            return page_number

    def getQiKanLieBiaoPageData(self, SearchStateJson, page):
        return {
            'SearchStateJson': SearchStateJson,
            'displaymode': 1,
            'pageindex': int(page),
            'pagecount': 21,
            'random': random.random()
        }

    def getQiKanList(self, resp):
        selector = Selector(text=resp)
        li_list = selector.xpath("//ul[@class='list_tup']/li")
        for li in li_list:
            title = li.xpath("./a/@title").extract_first()
            href = li.xpath("./a/@href").extract_first()
            if not title or not href:
                continue

            try:
                pcode = re.findall(r"pcode=(.*?)&", href)[0]
            except:
                continue
            try:
                pykm = re.findall(r"&baseid=(.*)", href)[0]
            except:
                continue

            url = "http://navi.cnki.net/knavi/JournalDetail?pcode={}&pykm={}".format(pcode, pykm)

            yield title, url


class QiKanLunWen_LunWenTaskServer(object):
    def __init__(self, logging):
        self.logging = logging

    # 生成单个知网期刊的时间列表种子
    def qiKanTimeListUrl(self, url, timelisturl):
        if re.findall(r'pcode=(\w+)&', url):
            pcode = re.findall(r'pcode=(\w+)&', url)[0]
        elif re.findall(r'pcode=(\w+)', url):
            pcode = re.findall(r'pcode=(\w+)', url)[0]
        else:
            pcode = None

        if re.findall(r'pykm=(\w+)&', url):
            pykm = re.findall(r'pykm=(\w+)&', url)[0]
        elif re.findall(r'pykm=(\w+)', url):
            pykm = re.findall(r'pykm=(\w+)', url)[0]
        else:
            pykm = None

        if not pcode or not pykm:
            return None

        qiKanTimeListUrl = timelisturl.format(pcode, pykm)

        return {"qiKanTimeListUrl": qiKanTimeListUrl, "pcode": pcode, "pykm": pykm}

    # 获取期刊【年】、【期】列表
    def getQiKanTimeList(self, resp):
        return_data = []
        selector = Selector(text=resp)

        div_list = selector.xpath("//div[@class='yearissuepage']")

        for div in div_list:
            dl_list = div.xpath("./dl")

            for dl in dl_list:
                time_data = {}
                year = dl.xpath("./dt/em/text()").extract_first()
                if not year:
                    continue

                time_data[year] = []
                stage_list = dl.xpath("./dd/a/text()").extract()  # 期列表
                for stage in stage_list:
                    time_data[year].append(stage)
                return_data.append(time_data)

        return return_data

    # 获取论文列表页种子
    def getArticleListUrl(self, url, data, pcode, pykm):
        # 论文列表页种子 http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year=2018&issue=Z1&pykm=SHGJ&pageIdx=0&pcode=CJFD
        return_data = []
        try:
            year = str(list(data.keys())[0])
            stage_list = data[year]
        except:
            return return_data

        for stages in stage_list:
            try:
                stage = re.findall(r'No\.(.*)', stages)[0]
            except:
                continue

            list_url = url.format(year, stage, pykm, pcode)
            return_data.append(list_url)

        return return_data

    # 获取文章种子列表
    def getArticleUrlList(self, resp, qiKanUrl, xuekeleibie):
        return_data = []
        index_url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode='
        selector = Selector(text=resp)
        dd_list = selector.xpath("//dd")
        for dd in dd_list:
            href_url = dd.xpath("./span[@class='name']/a/@href").extract_first()
            try:
                href_url = re.findall(r"dbCode=(.*?)&url=", href_url)[0]
            except:
                continue

            url = index_url + href_url
            return_data.append({'sha': hashlib.sha1(url.encode()).hexdigest(),
                                'url': url,
                                'qiKanUrl': qiKanUrl,
                                'xueKeLeiBie': xuekeleibie})

        return return_data


class QiKanLunWen_LunWenDataServer(Server):
    def __init__(self, logging):
        self.logging = logging

    def getTask(self, task_data):
        task = ast.literal_eval(re.sub(r"datetime\.datetime\(.*\)", '"' + "date" + '"', task_data))
        return ast.literal_eval(task['memo'])

    # 获取期刊名称
    def getQiKanMingCheng(self, resp):
        selector = Selector(text=resp)
        title = selector.xpath("//p[@class='title']/a/text()").extract_first()
        if not title:
            return ""

        return title

    # 获取时间【年】
    def getshiJian(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='sourinfo']/p")
        try:
            p = p_list[2]
        except:
            return {}

        try:
            shiJian = re.findall(r'(\d{4})年', p.xpath("./a/text()").extract_first())[0]
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
    def getYeShu(self, resp):
        yeShu = re.findall(r'<label>页数：</label><b>(\d+)</b>', str(resp))
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
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='author']/span/a")
        if not a_list:
            return ""

        name_list = []
        for a in a_list:
            name = a.xpath("./text()").extract()
            if name:
                name_list.append(name[0])

        return_data = '|'.join(name_list)

        return return_data

    # 获取文章标题
    def getArticleTitle(self, resp):
        selector = Selector(text=resp)
        title = selector.xpath("//h2[@class='title']/text()").extract_first()
        if not title:
            return ""

        return title

    # 获取关联企业机构
    def getGuanLianQiYeJiGou(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='orgn']/span/a")
        for a in a_list:
            url_data = a.xpath("./@onclick").extract_first()
            if not url_data:
                continue

            try:
                url_data = eval(re.findall(r"(\(.*\))", url_data)[0])
            except:
                continue

            sfield = url_data[0]
            skey = parse.quote(url_data[1])
            code = url_data[2]
            url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                   'sfield={}&skey={}&code={}'.format(sfield, skey, code))
            url_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()

            return_data.append({'url': url, 'ss': '机构', 'sha': url_sha1})

        return return_data

    # 获取PDF下载链接
    def getXiaZai(self, resp):
        selector = Selector(text=resp)
        download_url = selector.xpath("//a[@id='pdfDown']/@href").extract_first()
        if not download_url:
            return ""

        if re.search(r"http", download_url):
            return ''.join(re.findall(r"[^\n\s']", download_url))
        else:
            return 'http://kns.cnki.net' + ''.join(re.findall(r"[^\n\s']", download_url))

    # 获取关键词
    def getGuanJianCi(self, resp):
        return_data = []
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '关键词' in title:
                a_list = p.xpath("./a")
                for a in a_list:
                    a_text = a.xpath("./text()").extract_first()
                    if not a_text:
                        continue

                    guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;]', a_text))

                    return_data.append(guanJianCi)

        return '|'.join(return_data)

    # 获取作者单位
    def getZuoZheDanWei(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='orgn']/span/a")
        for a in a_list:
            url_data = a.xpath("./@onclick").extract_first()
            if not url_data:
                continue
            try:
                url_data = eval(re.findall(r"(\(.*\))", url_data)[0])
            except:
                continue

            zuoZheDanWei = url_data[1]
            return_data.append(zuoZheDanWei)

        return '|'.join(return_data)

    # 获取大小
    def getDaXiao(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        if not span_list:
            return {}

        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '大小' in title:
                daXiao = span.xpath("./b/text()").extract_first()
                if daXiao:
                    try:
                        v = re.findall(r'\d+', daXiao)[0]
                    except:
                        v = ''
                    try:
                        u = re.findall(r"[^\d]", daXiao)[0]
                    except:
                        u = 'K'

                    return {'v': v, 'u': u}
                else:

                    return {}

    # 获取在线阅读地址
    def getZaiXianYueDu(self, resp):
        selector = Selector(text=resp)
        read_url = selector.xpath("//a[@class='icon icon-dlcrsp xml']/@href").extract_first()
        if not read_url:
            return ""

        if re.search(r"http", read_url):
            return read_url

        return 'http://kns.cnki.net' + read_url

    # 获取分类号
    def getZhongTuFenLeiHao(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        if not p_list:
            return ""

        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '分类号' in title:
                fenLeiHao = p.xpath("./text()").extract_first()
                if not fenLeiHao:
                    return ""

                return ''.join(re.sub(';', '|', fenLeiHao))

        return ""

    # 获取下载次数
    def getXiaZaiCiShu(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        if not span_list:
            return ""

        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '下载' in title:
                xiaZaiCiShu = span.xpath("./b/text()").extract_first()
                if not xiaZaiCiShu:
                    return ""

                return xiaZaiCiShu

        return ""

    # 获取期号
    def getQiHao(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='sourinfo']/p")
        if not p_list:
            return ""

        p = p_list[2]
        qiHao = p.xpath("./a/text()").extract_first()
        if qiHao:
            return re.sub(r"(\r|\n|\s)", "", qiHao)

        qiHao = re.findall(r"(\d{4}年.*期)", resp)
        if qiHao:
            return re.sub(r"(\r|\n|\s)", "", qiHao[0])

        return ""

    # 获取所在页码
    def getSuoZaiYeMa(self, resp):
        selector = Selector(text=resp)
        span_list = selector.xpath("//div[@class='dllink-down']/div[@class='info']/div[@class='total']/span")
        if not span_list:
            return ""

        for span in span_list:
            title = span.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '页码' in title:
                xiaZaiYeMa = span.xpath("./b/text()").extract_first()
                if not xiaZaiYeMa:
                    return ""

                return xiaZaiYeMa

        return ""

    # 获取摘要
    def getZhaiYao(self, resp):
        selector = Selector(text=resp)
        zhaiYao = selector.xpath("//span[@id='ChDivSummary']/text()").extract_first()
        if not zhaiYao:
            return ""

        return zhaiYao

    # 获取基金
    def getJiJin(self, resp):
        return_data = []
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if '基金' in title:
                a_list = p.xpath("./a")
                if a_list:
                    for a in a_list:
                        a_text = a.xpath("./text()").extract_first()
                        if not a_text:
                            continue

                        guanJianCi = ''.join(re.findall(r'[^&nbsp\r\n\s;；]', a_text))

                        return_data.append(guanJianCi)

        return '|'.join(return_data)

    # 获取doi
    def getDoi(self, resp):
        selector = Selector(text=resp)
        p_list = selector.xpath("//div[@class='wxBaseinfo']/p")
        if not p_list:
            return ""

        for p in p_list:
            title = p.xpath("./label/text()").extract_first()
            if not title:
                continue

            if 'DOI' in title:
                doi = p.xpath("./text()").extract_first()
                if not doi:
                    return ""

                return doi

        return ""

    # 获取关联人物
    def getGuanLianRenWu(self, resp):
        return_data = []
        selector = Selector(text=resp)
        a_list = selector.xpath("//div[@class='author']/span/a")
        for a in a_list:
            a_onclick = a.xpath("./@onclick").extract_first()
            if not a_onclick:
                continue
            try:
                url_data = ast.literal_eval(re.findall(r"(\(.*\))", a_onclick)[0])
            except:
                continue

            sfield = url_data[0]
            skey = parse.quote(url_data[1])
            code = url_data[2]
            if not sfield or not skey:
                continue

            url = ('http://kns.cnki.net/kcms/detail/knetsearch.aspx?'
                   'sfield={}'
                   '&skey={}'
                   '&code={}'.format(sfield, skey, code))
            sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
            name = a.xpath("./text()").extract_first()
            if not name:
                continue

            return_data.append({'sha': sha1, 'url': url, 'name': name, 'ss': '人物'})

        return return_data










