# -*-coding:utf-8-*-
'''
代理IP获取工具
'''
import os
import sys
import time
import json
import requests
import socket
import re

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from Utils import redispool_utils

# 检测代理IP是否是高匿代理， 高匿返回True， 否则返回Fales
def jianChaNiMingDu(proxy, logging):
    local_ip = ''
    proxy_ip = ''
    proxies = {
        'http': proxy,
        'https': proxy
    }
    print(proxies)
    # 获取本地IP
    local_resp = requests.get('https://httpbin.org/get')
    if local_resp.status_code == 200:
        local_ip = json.loads(local_resp.content.decode('utf-8'))['origin']
        logging.info('检测到本地IP: %s' % local_ip)

    # 获取使用代理返回IP
    proxy_resp = requests.get(url='https://httpbin.org/get', proxies=proxies)
    if proxy_resp.status_code == 200:
        proxy_ip = json.loads(proxy_resp.content.decode('utf-8'))['origin']
        logging.info('检测到代理ip: %s' % proxy_ip)

    # 判断代理是否高匿
    if local_ip not in proxy_ip:

        return True
    else:

        return False

def getZhiMaProxy_Number(num, protocol=2, time=1):
    '''
    按次从芝麻代理API获取代理
    :param num: 获取代理个数
    :param protocol: IP协议 1:HTTP 2:SOCK5 11:HTTPS
    :return: 
    '''
    url = ('http://webapi.http.zhimacangku.com/getip?'
           'num={}'  # 获取数量
           '&type=2'
           '&pro='
           '&city=0'
           '&yys=0'
           '&port={}'  # 代理协议
           '&time={}'
           '&ts=0'
           '&ys='
           '&cs=0'
           '&lb=1'
           '&sb=0'
           '&pb=45'
           '&mr=1'
           '&regions='.format(num, protocol, time))
    r = requests.get(url)
    if r.status_code == 200:
        text = r.text
        obj = json.loads(text)
        if obj['code'] == 0:
            return obj['data']
    else:
        return None

    return None

def getZhiMaProxy_SetMeal(set_meal, num, protocol=2, time=1):
    '''
    获取芝麻代理
    :param num: 获取数量
    :param protocol: 协议， 默认获取socks5
    :return: 代理列表
    '''
    pack = "{}".format(set_meal)
    url = ('http://webapi.http.zhimacangku.com/getip?'
           'num={}'  # 获取数量
           '&type=2'  # 返回类型（1TXT 2JSON 3html）
           '&pro='  # 省份
           '&city=0'  # 城市
           '&yys=0'  # 不限运营商
           '&port={}'  # IP协议（1:HTTP 2:SOCK5 11:HTTPS ）
           '&pack={}'  # 套餐号
           '&ts=0'
           '&ys=0'
           '&cs=0'
           '&lb=1'
           '&sb=0'
           '&pb=45'
           '&mr=1'  # 去重方式（1:360天去重 2:单日去重 3:不去重）
           '&regions='.format(num, protocol, pack))
    r = requests.get(url)
    if r.status_code == 200:
        text = r.text
        obj = json.loads(text)
        if obj['code'] == 0:
            return obj['data']
    else:
        return None

    return None

def getProxy(redis_client, logging):
    '''
    随机获取代理池短效代理IP
    :return: 代理IP
    '''
    for i in range(10):
        proxydata = redispool_utils.srandmember(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, num=1)
        if proxydata:
            proxy = proxydata[0]
            proxies = {
                'http': '{}'.format(proxy),
                'https': '{}'.format(proxy)
            }

            return proxies
        else:
            logging.error('代理池代理获取失败')
            time.sleep(1)
            continue

def getProxydemo(redis_client):
    '''
    随机获取代理池短效代理IP
    :return: 代理IP
    '''
    for i in range(10):
        proxydata = redispool_utils.srandmember(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, num=1)
        if proxydata:
            proxy = proxydata[0]
            proxies = {
                'http': '{}'.format(proxy),
                'https': '{}'.format(proxy)
            }

            return proxies
        else:
            # logging.error('代理池代理获取失败')
            time.sleep(1)
            continue

def delProxy(redis_client, proxies):
    '''
    删除代理池指定代理
    :param proxies: 当前代理
    '''
    proxy = proxies['http']
    redispool_utils.srem(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, value=proxy)

def getLocalIP():
    '''
    获取本机IP
    :return: 本机IP
    '''
    global s
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()

        return ip
    except:
        s.close()
        return None

# 获取阿布云动态版代理
def getABuYunProxy():
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"

    # 代理隧道验证信息
    proxyUser = "H1A955UYUR3S8RXD"
    proxyPass = "6FD2F11DD2337CF0"

    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
      "host" : proxyHost,
      "port" : proxyPort,
      "user" : proxyUser,
      "pass" : proxyPass,
    }

    proxies = {
        "http"  : proxyMeta,
        "https" : proxyMeta,
    }
    return proxies

# 获取redis长效代理
def getLangProxy(logging, redis_client):
    proxydata = redispool_utils.srandmember(redis_client=redis_client, key=settings.LANG_PROXY_KEY, num=1)
    if proxydata:
        proxy = proxydata[0]
        proxies = {
            'http': 'http://{}'.format(proxy),
            'https': 'https://{}'.format(proxy)
        }

        return proxies
    else:
        logging.error('长效代理获取失败')
        return None

# 获取adsl代理
def getAdslProxy(logging, random=0, country=1, city=0):
    url = "{}?random={}&country={}&city={}".format(settings.GET_PROXY_API, random, country, city)
    proxy_data = requests.get(url=url).content.decode('utf-8')
    data = json.loads(proxy_data)
    if data['status'] == 0:
        proxies = {
            'http': '{}'.format('http://{}:{}'.format(data['ip'], data['port'])),
            'https': '{}'.format('https://{}:{}'.format(data['ip'], data['port']))
        }

        return proxies

    else:
        logging.error('代理池代理获取失败')

# adsl代理状态更新
def updateAdslProxy(proxies):
    ip = re.findall(r"\d+\.\d+\.\d+\.\d+", proxies['http'])[0]
    url = "{}?ip={}".format(settings.UPDATE_PROXY_API, ip)
    requests.get(url=url)
    time.sleep(1)

