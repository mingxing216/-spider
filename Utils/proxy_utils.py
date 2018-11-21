# -*-coding:utf-8-*-
'''
代理IP获取工具
'''
import os
import sys
import time
import json
import requests

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from Utils import redispool_utils


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


def getLongProxy(redis_client, logging):
    '''
    随机获取代理池长效代理IP
    :return: 代理IP
    '''
    for i in range(10):
        proxydata = redispool_utils.srandmember(redis_client=redis_client, key=settings.REDIS_LONG_PROXY_KEY, num=1)
        if proxydata:
            proxy = proxydata[0]
            proxies = {
                'http': 'http://{}'.format(proxy),
                'https': 'https://{}'.format(proxy)
            }

            return proxies
        else:
            logging.error('代理池代理获取失败')
            time.sleep(1)
            continue


def delProxy(redis_client, proxies):
    '''
    删除代理池指定代理
    :param proxies: 当前代理
    '''
    proxy = proxies['http']
    redispool_utils.srem(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, value=proxy)