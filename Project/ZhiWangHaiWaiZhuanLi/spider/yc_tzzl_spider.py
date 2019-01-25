#-*-coding:utf-8-*-
import sys
import os
import re
import requests
import ast
import copy
import pprint
from urllib.parse import unquote
from lxml import html

etree = html.etree

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import user_agent_u


# 从入口页获取第一部分cookie和默认同族页post参数
def func1(resp):
    return_data = {}
    # # url = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?dbcode=SOPD&dbname=SOPD2018&filename=CA2355466(A1)'
    #
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    # }
    #
    # # 获取cookie
    # resp = requests.get(url=url, headers=headers)
    resp_headers = resp.headers
    resp_headers_cookie = resp_headers.get('Set-Cookie')
    session_id = re.findall(r"ASP\.NET_SessionId=(.*?;)", resp_headers_cookie)[0]
    sid = re.findall(r"SID=(.*?;)", resp_headers_cookie)[0]
    autoiplogin = re.findall(r"AutoIpLogin=(.*?;)", resp_headers_cookie)[0]
    lid = re.findall(r"LID=(.*?;)", resp_headers_cookie)[0]
    cookie = 'ASP.NET_SessionId=' + session_id + ' ' + 'AutoIpLogin=' + autoiplogin + ' ' + 'LID=' + lid + ' ' + 'SID=' + sid

    # 获取同族专利post请求参数
    resp_response = resp.content.decode('utf-8')
    tzzl_data = re.findall(r"var tzzl_data = ({.*?});", resp_response)[0]

    return_data['cookie'] = cookie
    return_data['tzzl_data'] = tzzl_data

    return return_data


def func2(data1, proxies):
    url = 'http://dbpub.cnki.net/grid2008/dbpub/Detail.aspx?action=node&dbname=sopd&block=SOPD_TZZL'
    cookie = data1['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent_u.get_ua()
    }
    data = ast.literal_eval(data1['tzzl_data'])
    try:
        resp = requests.post(url=url, headers=headers, data=data, proxies=proxies, timeout=5).content.decode('utf-8')
    except:
        resp = None
    if not resp:
        return None
    resp_etree = etree.HTML(resp)
    try:
        more_url = 'http://dbpub.cnki.net/grid2008/dbpub/' + resp_etree.xpath("//a[contains(text(), '更多')]/@href")[0]
        data1['more_url'] = more_url
    except:
        data1['more_url'] = None
    
    data1['yc_tzzl_html'] = resp
    return data1


def func3(data2, proxies):
    url = data2['more_url']
    if url is None:
        return None
    cookie = data2['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent_u.get_ua()
    }
    try:
        resp = requests.get(url=url, headers=headers, proxies=proxies, allow_redirects=False, timeout=5).content.decode('utf-8')
    except:
        resp = None
    resp_etree = etree.HTML(resp)
    try:
        redisect_url = 'http://dbpub.cnki.net' + resp_etree.xpath("//a/@href")[0]
    except:
        return None
    data2['redisect_url'] = redisect_url

    return data2


def func4(data3, proxies, save_data, server):
    save_data['guanLianTongZuZhuanLi'] = []
    url = unquote(data3['redisect_url'])
    cookie = data3['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent_u.get_ua()
    }
    try:
        resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=5)
    except:
        resp = None
    # 生成完整cookie
    resp_headers = resp.headers
    resp_headers_cookie = resp_headers.get('Set-Cookie')
    c_m_linid = re.findall(r"c_m_LinID=(.*?;)", resp_headers_cookie)[0]
    c_m_expire = re.findall(r"c_m_expire=(.*?;)", resp_headers_cookie)[0]
    new_cookie = cookie + ' ' + 'c_m_LinID=' + c_m_linid + ' ' + 'c_m_expire=' + c_m_expire + ' ' + 'FileNameM=cnki%3A'
    # data3['cookie'] = new_cookie

    resp_response = resp.content.decode('utf-8')
    resp_response_etree = etree.HTML(resp_response)
    # TODO 这里可以获取首页显示的所有同族专利数据
    data_list = server.getYcTzzlData(resp)
    for tzzl_data in data_list:
        save_data['guanLianTongZuZhuanLi'].append(tzzl_data)

    # TODO 暂时忽略专利数据， 只获取下一页地址
    try:
        next_yc_tzzl_url = 'http://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + \
                           resp_response_etree.xpath("//div[@id='id_grid_turnpage']/a[contains(text(), '下页')]/@href")[0]
    except:
        next_yc_tzzl_url = None

    while 1:
        # 抓取数据
        data = func5(next_yc_tzzl_url, proxies, new_cookie, save_data, server)
        if data is None:
            break
        next_yc_tzzl_url = data

    # return save_data

def func5(url, proxies, cookie, save_data, server):
    if url is None:
        return None

    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent_u.get_ua()
    }
    try:
        resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=5)
    except:
        resp = None
    # TODO 这里可以获取首页显示的所有同族专利数据
    data_list = server.getYcTzzlData(resp)
    for tzzl_data in data_list:
        save_data['guanLianTongZuZhuanLi'].append(tzzl_data)

    # 获取下一页
    resp_response = resp.content.decode('utf-8')
    resp_response_etree = etree.HTML(resp_response)
    try:
        next_yc_tzzl_url = 'http://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + \
                           resp_response_etree.xpath("//div[@id='id_grid_turnpage']/a[contains(text(), '下页')]/@href")[0]
    except:
        next_yc_tzzl_url = None

    return next_yc_tzzl_url

def func6(resp, save_data):
    save_data['guanLianTongZuZhuanLi'] = []
    resp_etree = etree.HTML(resp)
    a_list = resp_etree.xpath("//a")
    for a in a_list:
        data = {}
        try:
            data['title'] = a.xpath("./text()")[0]
        except:
            data['title'] = ''
        try:
            data['url'] = 'http://dbpub.cnki.net/grid2008/dbpub/' + a.xpath("./@href")[0]
        except:
            data['url'] = ''
        if data not in save_data['guanLianTongZuZhuanLi']:
            save_data['guanLianTongZuZhuanLi'].append(data)

def run(resp, proxies, save_data, server):
    # 从入口页获取第一部分cookie和默认同族页post参数
    data1 = func1(resp)
    # 从默认同族页获取隐藏同族页url
    data2 = func2(data1, proxies)
    if not data2:
        # 说明没有同族专利
        save_data['guanLianTongZuZhuanLi'] = []
        return
    # 从隐藏同族页获取重定向url
    data3 = func3(data2, proxies)
    if not data3:
        # 说明没有隐藏同族专利, 直接获取当前页显示同族
        func6(data2['yc_tzzl_html'], save_data)
    else:
        # 从重定向页获取完成cookie
        func4(data3, proxies, save_data, server)














