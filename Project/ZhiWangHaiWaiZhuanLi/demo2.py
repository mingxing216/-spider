import re
import requests
import ast
from urllib.parse import unquote
from lxml import html

etree = html.etree

# 从入口页获取第一部分cookie和默认同族页post参数
def func1(url):
    return_data = {}
    # url = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?dbcode=SOPD&dbname=SOPD2018&filename=CA2355466(A1)'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }

    # 获取cookie
    resp = requests.get(url=url, headers=headers)
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

def func2(data1):
    url = 'http://dbpub.cnki.net/grid2008/dbpub/Detail.aspx?action=node&dbname=sopd&block=SOPD_TZZL'
    cookie = data1['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    data = ast.literal_eval(data1['tzzl_data'])
    resp = requests.post(url=url, headers=headers, data=data).content.decode('utf-8')
    resp_etree = etree.HTML(resp)
    more_url = 'http://dbpub.cnki.net/grid2008/dbpub/' + resp_etree.xpath("//a[contains(text(), '更多')]/@href")[0]
    data1['more_url'] = more_url

    return data1

def func3(data2):
    url = data2['more_url']
    cookie = data2['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers, allow_redirects=False).content.decode('utf-8')
    resp_etree = etree.HTML(resp)
    redisect_url = 'http://dbpub.cnki.net' + resp_etree.xpath("//a/@href")[0]
    data2['redisect_url'] = redisect_url
    
    return data2

def func4(data3):
    url = unquote(data3['redisect_url'])
    cookie = data3['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)

    # 生成完整cookie
    resp_headers = resp.headers
    resp_headers_cookie = resp_headers.get('Set-Cookie')
    c_m_linid = re.findall(r"c_m_LinID=(.*?;)", resp_headers_cookie)[0]
    c_m_expire = re.findall(r"c_m_expire=(.*?;)", resp_headers_cookie)[0]
    new_cookie = cookie + ' ' + 'c_m_LinID=' + c_m_linid + ' ' + 'c_m_expire=' + c_m_expire + ' ' + 'FileNameM=cnki%3A'
    data3['cookie'] = new_cookie

    # TODO 这里可以获取首页显示的所有同族专利数据
    # TODO 暂时忽略专利数据， 只获取下一页地址
    resp_response = resp.content.decode('utf-8')
    resp_response_etree = etree.HTML(resp_response)
    next_yc_tzzl_url = 'http://dbpub.cnki.net/grid2008/dbpub/brief.aspx' + \
                       resp_response_etree.xpath("//div[@id='id_grid_turnpage']/a[contains(text(), '下页')]/@href")[0]

    data3['next_page'] = next_yc_tzzl_url

    return data3

def func5(data4):
    url = data4['next_page']
    cookie = data4['cookie']
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }

    resp = requests.get(url=url, headers=headers).content.decode('utf-8')
    print(resp)


def run(url):
    # 从入口页获取第一部分cookie和默认同族页post参数
    data1 = func1(url)
    # 从默认同族页获取隐藏同族页url
    data2 = func2(data1)
    # 从隐藏同族页获取重定向url
    data3 = func3(data2)
    # 从重定向页获取完成cookie
    data4 = func4(data3)
    # 获取下一页响应
    func5(data4)


run('http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?dbcode=SOPD&dbname=SOPD2018&filename=CA2355466(A1)')











