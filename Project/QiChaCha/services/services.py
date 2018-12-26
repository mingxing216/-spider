# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import requests
import json
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import proxy_utils
from Utils import create_ua_utils
from Project.QiChaCha.dao import dao

etree = html.etree

# 服务_基于登录
class Services_Logging(object):
    def __init__(self):
        pass

    # 获取地区分类url列表
    def getAddUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//ul[@class='sidebar-hangye-list']/li/a"):
            a_list = resp_etree.xpath("//ul[@class='sidebar-hangye-list']/li/a")
            for a in a_list:
                add_name = a.xpath("./text()")[0]
                add_url = 'https://www.qichacha.com' + a.xpath("./@href")[0] + '_1.html'
                logging.info('已获取地区分类url  {}: {}'.format(add_name, add_url))
                return_data.append(add_url)

            return return_data

        logging.error('获取地区分类url失败')
        return return_data

    # 获取行业分类url列表
    def getIndustryUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='col-md-8 columns']/ul/li/a"):
            a_list = resp_etree.xpath("//div[@class='col-md-8 columns']/ul/li/a")
            for a in a_list:
                add_name = a.xpath("./text()")[0]
                # https://www.qichacha.com/gongsi_industry.shtml?industryCode=M&subIndustryCode=74&p=2
                industryCode = re.findall(r"_(.+)_", a.xpath("./@href")[0])[0]
                subIndustryCode = re.findall(r"_.+_(\d+)", a.xpath("./@href")[0])[0]
                add_url = 'https://www.qichacha.com/gongsi_industry.shtml?industryCode={}&subIndustryCode={}&p=1'.format(industryCode, subIndustryCode)
                logging.info('已获取地区分类url  {}: {}'.format(add_name, add_url))
                return_data.append(add_url)

            return return_data

        logging.error('获取行业分类url失败')
        return return_data

    # 获取企业url列表
    def getCompanyUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='searchlist']"):
            url_list = resp_etree.xpath("//section[@id='searchlist']/a/@href")
            for url in url_list:
                re_url = re.sub(r"_.*_", "_", url)
                save_url = 'https://www.qichacha.com' + re_url
                logging.info('已获取企业url: {}'.format(save_url))
                return_data.append(save_url)


            return return_data

        logging.error('获取企业url失败')
        return return_data


# 服务_字段提取
class Services_GetData(object):
    def __init__(self):
        self.dao = dao.Dao()


    # 判断页面是否加载成功
    def getHtmlStatus(self, loggong, resp_pc, resp_mobile):
        resp_pc_etree = etree.HTML(resp_pc)
        resp_mobile_etree = etree.HTML(resp_mobile)
        if len(resp_pc) < 200 or len(resp_mobile) < 200:

            return {'status': 1}
        elif resp_pc_etree.xpath("//div[@class='imgkuang']") and resp_mobile_etree.xpath("//div[@class='company-name']/text()"):

            return {'status': 0}

        else:

            return {'status': 2}

    # 获取标题
    def getTitle(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='company-name']/text()"):
            title = re.sub(r"(\r|\n|&nbsp|\s+)", "", resp_etree.xpath("//div[@class='company-name']/text()")[0])

            return title

        return ""

    # 获取标识
    def getBiaoShi(self, logging, resp):
        if re.findall(r"https://img\.qichacha\.com/Product/.*?\.jpg", resp):
            img_url = re.findall(r"https://img\.qichacha\.com/Product/.*?\.jpg", resp)[0]
            proxies = proxy_utils.getAdslProxy(logging=logging)
            headers = {
                'user-agent': create_ua_utils.get_ua()
            }
            img_resp = requests.get(url=img_url, headers=headers, proxies=proxies).content
            self.dao.saveImg(logging=logging, media_url=img_url, content=img_resp, type='image')

            return img_url

        return ""

    # 获取邮箱
    def getEmail(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//a[@class='email a-decoration']/text()"):

            return resp_etree.xpath("//a[@class='email a-decoration']/text()")[0]

        return ""

    # 获取简介
    def getJianJie(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='m-t-sm m-b-sm']//text()"):
            return re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", ''.join(resp_etree.xpath("//div[@class='m-t-sm m-b-sm']//text()")))

        return ""

    # 获取主页
    def getZhuYe(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//span[text()='官网：']/following-sibling::span[1]/a/@href"):

            return resp_etree.xpath("//span[text()='官网：']/following-sibling::span[1]/a/@href")[0]

        return ""

    # 获取所在地_内
    def getSuoZaiDi_Nei(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='address']/text()"):

            return re.sub(r"(\r|\n|&nbsp|\s+)", "", resp_etree.xpath("//div[@class='address']/text()")[0])

        return ""

    # 获取点击量
    def getDianJiLiang(self, resp):
        if re.findall(r"<span>浏览：(.*?)</span>", resp):

            return re.findall(r"<span>浏览：(.*?)</span>", resp)[0]

        return ""

    # 获取电话
    def getDianHua(self, resp):
        try:
            data = json.loads(resp)
            return_data = data['data']['PhoneNumber']
            if return_data:
                return return_data

            return ""

        except:
            return ""

    # 获取开户银行
    def getKaiHuYinHang(self, resp):
        try:
            data = json.loads(resp)
            return_data = data['data']['Bank']
            if return_data:
                return return_data

            return ""

        except:
            return ""

    # 获取银行账号
    def getYinHangZhangHao(self, resp):
        try:
            data = json.loads(resp)
            return_data = data['data']['Bankaccount']
            if return_data:
                return return_data

            return ""

        except:
            return ""

    # 获取法定代表人
    def getFaDingDaiBiaoRen(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//a[@class='oper']/text()"):

            return re.sub(r"(\r|\n|&nbsp|\s+)", "", resp_etree.xpath("//a[@class='oper']/text()")[0])

        return ""

    # 获取注册资本
    def getZhuCeZiBen(self, resp):
        return_data = {}
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[text()='注册资本']/following-sibling::div[1]/text()"):
            return_data['v'] = re.sub(r"(\r|\n|&nbsp|\s+|[\u4e00-\u9fa5])", "", resp_etree.xpath("//div[text()='注册资本']/following-sibling::div[1]/text()")[0])
            return_data['u'] = '万元'
            return return_data

        return return_data

    # 获取企业状态
    def getJingYingZhuangTai(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[text()='企业状态']/following-sibling::div[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "", resp_etree.xpath("//div[text()='企业状态']/following-sibling::div[1]/text()")[0])

        return ""

    # 获取统一社会信
    def getTongYiSheHuiXin(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[text()='统一社会信用代码']/following-sibling::div[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "",
                          resp_etree.xpath("//div[text()='统一社会信用代码']/following-sibling::div[1]/text()")[0])

        return ""

    # 获取注册号
    def getZhuCeHao(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[text()='注册号']/following-sibling::div[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "",
                          resp_etree.xpath("//div[text()='注册号']/following-sibling::div[1]/text()")[0])

        return ""

    # 获取企业类型
    def getQiYeLeiXing(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[text()='企业类型']/following-sibling::div[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "",
                          resp_etree.xpath("//div[text()='企业类型']/following-sibling::div[1]/text()")[0])

        return ""

    # 获取核准日期
    def getHeZhunRiQi(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[text()='核准日期：']/following-sibling::td[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "",
                          resp_etree.xpath("//td[text()='核准日期：']/following-sibling::td[1]/text()")[0]) + ' ' + '00:00:00'

        return ""

    # 获取所在地_筛
    def getSuoZaiDi_Shai(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[text()='所属地区：']/following-sibling::td[1]/text()"):
            return re.sub(r"(\r|\n|&nbsp|\s+)", "",
                          resp_etree.xpath("//td[text()='所属地区：']/following-sibling::td[1]/text()")[0])

        return ""

    # 获取曾用名
    def getCengYongMing(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '曾用名')]/following-sibling::td[1]/span/text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(resp_etree.xpath("//td[contains(text(), '曾用名')]/following-sibling::td[1]/span/text()")))
        if resp_etree.xpath("//td[contains(text(), '曾用名')]/following-sibling::td[1]/text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", resp_etree.xpath("//td[contains(text(), '曾用名')]/following-sibling::td[1]/text()")[0])

        return ""

    # 获取员工人数
    def getYuanGongRenShu(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '人员规模')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath("//td[contains(text(), '人员规模')]/following-sibling::td[1]//text()")))

        return ""

    # 获取经营范围
    def getJingYingFanWei(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '经营范围')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath("//td[contains(text(), '经营范围')]/following-sibling::td[1]//text()")))

        return ""

    # 获取实缴资本
    def getShiJiaoZiBen(self, resp):
        return_data = {}
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '实缴资本')]/following-sibling::td[1]//text()"):
            return_data['v'] = re.sub(r"(\r|\n|\t|&nbsp|\s+|[\u4e00-\u9fa5])", "", '|'.join(
                resp_etree.xpath("//td[contains(text(), '实缴资本')]/following-sibling::td[1]//text()")))
            return_data['u'] = '万元'

        return ""

    # 获取成立日期
    def getChengLiRiQi(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '成立日期')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath("//td[contains(text(), '成立日期')]/following-sibling::td[1]//text()"))) + ' ' + '00:00:00'

        return ""

    # 获取纳税人识别
    def getNaShuRenShiBie(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '纳税人识别号')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '纳税人识别号')]/following-sibling::td[1]//text()")))

        return ""

    # 获取组织机构代码
    def getZuZhiJiGouDaiMa(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '组织机构代码')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '组织机构代码')]/following-sibling::td[1]//text()")))

        return ""

    # 获取主营行业
    def getZhuYingHangYe(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '所属行业')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '所属行业')]/following-sibling::td[1]//text()")))

        return ""

    # 获取登记机关
    def getDengJiJiGuan(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '登记机关')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '登记机关')]/following-sibling::td[1]//text()")))

        return ""

    # 获取英文名
    def getYingWenMing(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '英文名')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '英文名')]/following-sibling::td[1]//text()")))

        return ""

    # 获取参保人数
    def getCanBaoRenShu(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '参保人数')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '参保人数')]/following-sibling::td[1]//text()")))

        return ""

    # 获取营业期限
    def getYingYeQiXian(self, resp):
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//td[contains(text(), '营业期限')]/following-sibling::td[1]//text()"):
            return re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", '|'.join(
                resp_etree.xpath(
                    "//td[contains(text(), '营业期限')]/following-sibling::td[1]//text()")))

        return ""

    # 获取股东信息
    def getGuDongXinXi(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='Sockinfo']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='Sockinfo']/table/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['guDongFaQiRen'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", tr.xpath(".//h3[@class='seo font-14']/text()")[0])
                        else:
                            data['guDongFaQiRen'] = ""
                        if td.xpath(".//h3[@class='seo font-14']/../@href"):
                            data['url'] = "https://www.qichacha.com" + td.xpath(".//h3[@class='seo font-14']/../@href")[0]
                        else:
                            data['url'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data['chiGuBiLi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['chiGuBiLi'] = ""
                    if td_list.index(td) == 3:
                        if td.xpath("./text()"):
                            data['renJiaoChuZiE'] = {'v': re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0]), 'u': '万元'}
                        else:
                            data['renJiaoChuZiE'] = {}
                    if td_list.index(td) == 4:
                        if td.xpath("./text()"):
                            data['renJiaoChuZiRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['renJiaoChuZiRiQi'] = ""
                return_data.append(data)

            return return_data

        return return_data

    # 获取股东及出资信息
    def getGuDongJiChuZiXinXi(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='StockHolders']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='StockHolders']/table/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['guDongFaQiRen'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                           tr.xpath(".//h3[@class='seo font-14']/text()")[0])
                        else:
                            data['guDongFaQiRen'] = ""
                        if td.xpath(".//h3[@class='seo font-14']/../@href"):
                            data['url'] = "https://www.qichacha.com" + td.xpath(".//h3[@class='seo font-14']/../@href")[
                                0]
                        else:
                            data['url'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data['chiGuBiLi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['chiGuBiLi'] = ""
                    if td_list.index(td) == 3:
                        if td.xpath("./text()"):
                            data['renJiaoChuZiE'] = {'v': re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0]), 'u': '万元'}
                        else:
                            data['renJiaoChuZiE'] = {}
                    if td_list.index(td) == 4:
                        if td.xpath("./text()"):
                            data['renJiaoChuZiRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['renJiaoChuZiRiQi'] = ""
                    if td_list.index(td) == 5:
                        if td.xpath("./text()"):
                            data['shiJiaoChuZiE'] = {'v': re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0]), 'u': '万元'}
                        else:
                            data['shiJiaoChuZiE'] = {}
                    if td_list.index(td) == 6:
                        if td.xpath("./text()"):
                            data['shiJiaoChuZiRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['shiJiaoChuZiRiQi'] = ""
                return_data.append(data)

            return return_data

        return return_data

    # 获取股权变更信息
    def getGuQuanBianGengXinXi(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='StockChange']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='StockChange']/table/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['guDongFaQiRen'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                           tr.xpath(".//h3[@class='seo font-14']/text()")[0])
                        else:
                            data['guDongFaQiRen'] = ""
                        if td.xpath(".//h3[@class='seo font-14']/../@href"):
                            data['url'] = re.sub(r"\.html", "", re.sub(r"firm_", "cbase_", "https://www.qichacha.com" + td.xpath(".//h3[@class='seo font-14']/../@href")[0]))
                        else:
                            data['url'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data['bianGengQianGuQuanBiLi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['bianGengQianGuQuanBiLi'] = ""
                    if td_list.index(td) == 3:
                        if td.xpath("./text()"):
                            data['bianGengHouGuQuanBiLi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['bianGengHouGuQuanBiLi'] = ""
                    if td_list.index(td) == 4:
                        if td.xpath("./text()"):
                            data['guQuanBianGengRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                              td.xpath("./text()")[0])
                        else:
                            data['guQuanBianGengRiQi'] = ""
                    if td_list.index(td) == 5:
                        if td.xpath("./text()"):
                            data['gongShiRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['gongShiRiQi'] = ""
                return_data.append(data)

            return return_data

        return return_data

    # 获取对外投资
    def getDuiWaiTouZi(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='touzilist']/table/tbody/tr"):
            tr_list = resp_etree.xpath("//section[@id='touzilist']/table/tbody/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['beiTouZiQiYeMingCheng'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath(".//h3[@class='seo font-14']/text()")[0])
                        else:
                            data['beiTouZiQiYeMingCheng'] = ""
                        if td.xpath(".//h3[@class='seo font-14']/../@href"):
                            data['qiYeUrl'] = re.sub(r"\.html", "", re.sub(r"firm_", "cbase_", "https://www.qichacha.com" +
                                                                       td.xpath(".//h3[@class='seo font-14']/../@href")[
                                                                           0]))
                        else:
                            data['qiYeUrl'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['beiTouZiFaDingDaiBiaoRen'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                           tr.xpath(".//h3[@class='seo font-14']/text()")[1])
                        else:
                            data['beiTouZiFaDingDaiBiaoRen'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data['zhuCeZiBen'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                                    td.xpath("./text()")[0])
                        else:
                            data['zhuCeZiBen'] = ""
                    if td_list.index(td) == 3:
                        if td.xpath("./text()"):
                            data['chuZiBiLi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['chuZiBiLi'] = ""
                    if td_list.index(td) == 4:
                        if td.xpath("./text()"):
                            data['chengLiRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                                td.xpath("./text()")[0])
                        else:
                            data['chengLiRiQi'] = ""
                    if td_list.index(td) == 5:
                        if td.xpath("./span/text()"):
                            data['zhuangTai'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./span/text()")[0])
                        else:
                            data['zhuangTai'] = ""
                return_data.append(data)

            return return_data

        return return_data

    # 获取主要人员
    def getZhuYaoRenYuan(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='Mainmember']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='Mainmember']/table/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath(".//h3[@class='seo font-14']/text()"):
                            data['xingMing'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "",
                                                           tr.xpath(".//h3[@class='seo font-14']/text()")[0])
                        else:
                            data['xingMing'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data['zhiWu'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['zhiWu'] = ""

                return_data.append(data)

            return return_data

        return return_data

    # 获取分支机构
    def getFenZhiJiGou(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='Subcom']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='Subcom']/table/tr")
            for tr in tr_list:
                data1 = {}
                data2 = {}
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data1['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data1['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath("./div/a/span/text()"):
                            data1['title'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./div/a/span/text()")[0])
                        else:
                            data1['title'] = ""
                        if td.xpath("./div/a/@href"):
                            url = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./div/a/@href")[0])
                            if re.match(r"http", url):
                                data1['url'] = url
                            else:
                                data1['url'] = re.sub(r"\.http", "", re.sub(r"firm_", 'cbase_', "https://www.qichacha.com" + url))
                        else:
                            data1['url'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            data2['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data2['xuHao'] = ""
                    if td_list.index(td) == 3:
                        if td.xpath("./div/a/span/text()"):
                            data2['title'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./div/a/span/text()")[0])
                        else:
                            data2['title'] = ""
                        if td.xpath("./div/a/@href"):
                            url = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./div/a/@href")[0])
                            if re.match(r"http", url):
                                data2['url'] = url
                            else:
                                data2['url'] = re.sub(r"\.http", "", re.sub(r"firm_", 'cbase_', "https://www.qichacha.com" + url))
                        else:
                            data2['url'] = ""

                if data1:
                    return_data.append(data1)
                if data2:
                    return_data.append(data2)

            return return_data

        return return_data

    # 获取变更记录
    def getBianGengJiLu(self, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='Changelist']/table/tr"):
            tr_list = resp_etree.xpath("//section[@id='Changelist']/table/tr")
            for tr in tr_list:
                data = {}
                if tr_list.index(tr) == 0:
                    continue
                td_list = tr.xpath("./td")
                for td in td_list:
                    if td_list.index(td) == 0:
                        if td.xpath("./text()"):
                            data['xuHao'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['xuHao'] = ""
                    if td_list.index(td) == 1:
                        if td.xpath("./text()"):
                            data['bianGengRiQi'] = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            data['bianGengRiQi'] = ""
                    if td_list.index(td) == 2:
                        if td.xpath("./text()"):
                            first_data = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./text()")[0])
                        else:
                            first_data = ""
                        if td.xpath("./span/text()"):
                            last_data = re.sub(r"(\r|\n|\t|\s+|&nbsp)", "", td.xpath("./span/text()")[0])
                        else:
                            last_data = ""
                        if first_data and last_data:
                            data['bianGengXiangMu'] = first_data + '(' + last_data + ')'
                        elif first_data:
                            data['bianGengXiangMu'] = first_data
                        else:
                            data['bianGengXiangMu'] = last_data
                    if td_list.index(td) == 3:
                        if td.xpath("./div//text()"):
                            data['bianGengQian'] = re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", ''.join(td.xpath("./div//text()")))
                        else:
                            data['bianGengQian'] = ""
                    if td_list.index(td) == 4:
                        if td.xpath("./div//text()"):
                            data['bianGengHou'] = re.sub(r"(\r|\n|\t|&nbsp|\s+)", "", ''.join(td.xpath("./div//text()")))
                        else:
                            data['bianGengHou'] = ""

                return_data.append(data)

            return return_data

        return return_data
