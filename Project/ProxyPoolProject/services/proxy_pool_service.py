# -*-coding:utf-8-*-
import sys
import os
import requests
import json
sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
# from Utils import redis_dbutils
from Utils import redispool_utils
import settings

class ProxyServices(object):

    def __init__(self):
        # self.neek = settings.NEEK
        # self.appkey = settings.APPKEY
        pass

    def createAccountBalanceApi(self, neek, appkey):
        '''
        生成账户余额查询api
        :return: 账户余额查询api
        '''

        api = 'http://web.http.cnapi.cc/index/index/get_my_balance?neek={}&appkey={}'.format(neek, appkey)

        return api

    def getZhiMaProxy(self, num, protocol=2):
        '''
        获取芝麻代理
        :param num: 获取数量
        :param protocol: 协议， 默认获取socks5
        :return: 代理列表
        '''
        url = ('http://webapi.http.zhimacangku.com/getip?'
               'num={}' # 获取数量
               '&type=2'
               '&pro='
               '&city=0'
               '&yys=0'
               '&port={}' # 代理协议
               '&time=1'
               '&ts=0'
               '&ys='
               '&cs=0'
               '&lb=1'
               '&sb=0'
               '&pb=45'
               '&mr=1'
               '&regions='.format(num, protocol))
        r = requests.get(url)
        if r.status_code == 200:
            text = r.text
            obj = json.loads(text)
            if obj['code'] == 0:

                return obj['data']
        else:
            return None

        return None


    def getProxyPoolLen(self,redis_client, key):
        '''
        获取代理池内代理数量
        :param key: redis中存储代理ip的集合名
        :return: 代理数量
        '''
        proxy_number = redispool_utils.scard(redis_client=redis_client, key=key)

        return proxy_number


class ProxySetMealServices(object):

    def __init__(self):
        self.set_meal = settings.ZHIMA_SETMEAL
        self.neek = settings.SETMEALNEEK
        self.appkey = settings.SETMEALAPPKEY
        self.ac = settings.AC

    def getZhiMaProxy(self, num, protocol=2):
        '''
        获取芝麻代理
        :param num: 获取数量
        :param protocol: 协议， 默认获取socks5
        :return: 代理列表
        '''
        pack = "{}".format(self.set_meal)
        url = ('http://webapi.http.zhimacangku.com/getip?'
             'num={}' # 获取数量
             '&type=2' # 返回类型（1TXT 2JSON 3html）
             '&pro=' # 省份
             '&city=0' # 城市
             '&yys=0' # 不限运营商
             '&port={}' # IP协议（1:HTTP 2:SOCK5 11:HTTPS ）
             '&pack={}' # 套餐号
             '&ts=0'
             '&ys=0'
             '&cs=0'
             '&lb=1'
             '&sb=0'
             '&pb=45'
             '&mr=1' # 去重方式（1:360天去重 2:单日去重 3:不去重）
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

    def setMealProxyNumber(self):
        '''
        查询当前套餐可用代理数量
        '''
        url = ('http://web.http.cnapi.cc/index/index/get_my_package_balance?'
               'neek={}'
               '&appkey={}'
               '&ac={}'.format(self.neek, self.appkey, self.ac))
        r = requests.get(url)
        if r.status_code == 200:
            text = r.text
            obj = json.loads(text)
            if obj['code'] == 0:
                return obj['data']['package_balance']
        else:
            return None

        return None

    def getProxyPoolLen(self,redis_client, key):
        '''
        获取代理池内代理数量
        :param key: redis中存储代理ip的集合名
        :return: 代理数量
        '''
        proxy_number = redispool_utils.scard(redis_client=redis_client, key=key)

        return proxy_number

