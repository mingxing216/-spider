# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


# 获取专利分类url
def getPatentClassifyList(logging, resp):
    return_data = []
    resp_etree = etree.HTML(resp)
    a_list = resp_etree.xpath("//a[@class='link']")
    if a_list:
        for a in a_list:
            if a.xpath("./@href"):
                url = a.xpath("./@href")[0]
                return_data.append(url)

    return return_data

# 获取专利国别分类
def getCountryDatas(resp):
    return_data = []
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//div[@class='cluster']/div"):
        div_list = resp_etree.xpath("//div[@class='cluster']/div")
        for div in div_list:
            datas = div.xpath("./div[@class='hd clear']/span/text()")
            for data in datas:
                if data == '国家／组织':
                    a_list = div.xpath("./div[@class='bd']/p/a")
                    for a in a_list:
                        data = {}
                        data['country_name'] = a.xpath("./@title")[0]
                        data['country_url'] = 'http://s.wanfangdata.com.cn/Patent.aspx' + a.xpath("./@href")[0] + '&p={}'
                        return_data.append(data)

    return return_data

# 获取当前页的专利url列表
def getPatentUrlList(logging, resp):
    return_data = []
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//a[@class='title']"):
        a_list = resp_etree.xpath("//a[@class='title']")
        for a in a_list:
            url = a.xpath("./@href")[0]
            return_data.append(url)

    return return_data

# 获取专利列表总页数
def getPageSum(logging, resp):
    rest_etree = etree.HTML(resp)
    if rest_etree.xpath("//span[@class='page_link']/text()"):
        page_data = rest_etree.xpath("//span[@class='page_link']/text()")[0]
        page = re.findall(r"/(\d+)", page_data)[0]

        return page

    else:
        return 0

# 判断页面是否正常 <title>404 Page</title>
def getPageStatus(resp):
    try:
        title = re.findall(r"<title>(.*)</title>", resp)[0]
        if title == '404 Page':
            return False
        else:
            return True
    except:
        return False



# =================《字段摘取部分》==================

# 获取专利标题
def getTitle(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//div[@class='section-baseinfo']/h1/text()"):
        title_data = resp_etree.xpath("//div[@class='section-baseinfo']/h1/text()")[0]
        title = re.sub(r"(\r|\n|&nbsp)", '', title_data)

        return title

    if re.findall(r"<title>(.*)</title>", resp):
        title_data = re.findall(r"<title>(.*)</title>", resp)[0]
        title = re.sub(r"(\r|\n|&nbsp)", '', title_data)

        return title

    return ""

# 获取下载链接
def getXiaZai(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//a[@class='download']/@href"):

        return resp_etree.xpath("//a[@class='download']/@href")[0]

    return ""

# 获取在线阅读
def getZaiXianYueDu(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//a[@class='view']/@href"):

        return resp_etree.xpath("//a[@class='view']/@href")[0]

    return ""

# 获取摘要
def getZhaiYao(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//div[@class='text']/text()"):
        return resp_etree.xpath("//div[@class='text']/text()")[0]

    return ""

# 获取专利类型
def getZhuanLiLeiXing(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='专利类型：']/following-sibling::span[1]/text()"):

        return resp_etree.xpath("//span[text()='专利类型：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取申请号
def getShenQingHao(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='申请（专利）号：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='申请（专利）号：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取申请日
def getShenQingRi(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='申请日期：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='申请日期：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("日", "", re.sub("(年|月)", "-", data) + " " + "00:00:00")

        return return_data

    return ""

# 获取公开日
def getGongKaiRi(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='公开(公告)日：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='公开(公告)日：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("日", "", re.sub("(年|月)", "-", data) + " " + "00:00:00")

        return return_data

    return ""

# 获取公开号
def getGongKaiHao(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='公开(公告)号：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='公开(公告)号：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取IPC主分类号
def getIPCZhuFenLei(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='主分类号：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='主分类号：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("(,|，)", '|', data)

        return return_data

    return ""

# 获取IPC分类号
def getIPCFenLeiHao(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='分类号：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='分类号：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("(,|，)", '|', data)

        return return_data

    return ""

# 获取申请人
def getShenQingRen(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='申请（专利权）人：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='申请（专利权）人：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("(,|，)", '|', data)

        return return_data

    return ""

# 获取发明人
def getFaMingRen(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='发明（设计）人：']/following-sibling::span[1]/text()"):
        data = resp_etree.xpath("//span[text()='发明（设计）人：']/following-sibling::span[1]/text()")[0]
        return_data = re.sub("(,|，)", '|', data)

        return return_data

    return ""

# 获取申请人地址
def getShenQingRenDiZhi(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='主申请人地址：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='主申请人地址：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取代理机构
def getDaiLiJiGou(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='专利代理机构：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='专利代理机构：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取代理人
def getDaiLiRen(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='代理人：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='代理人：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取国省代码
def getGuoShengDaiMa(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='国别省市代码：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='国别省市代码：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取主权项
def getZhuQuanXiang(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='主权项：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='主权项：']/following-sibling::span[1]/text()")[0]

    return ""

# 获取专利状态
def getZhuanLiZhuangTai(resp):
    resp_etree = etree.HTML(resp)
    if resp_etree.xpath("//span[text()='法律状态：']/following-sibling::span[1]/text()"):
        return resp_etree.xpath("//span[text()='法律状态：']/following-sibling::span[1]/text()")[0]

    return ""
