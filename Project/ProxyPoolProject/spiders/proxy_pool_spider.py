# -*-coding:utf-8-*-

import requests
import re


def balanceSpider(url):
    '''
    代理账户余额查询
    :param url: 余额查询接口
    :return: 余额
    '''

    resp = requests.get(url)
    if resp.status_code is 200:
        response = resp.content.decode('utf-8')
        balance = float(re.findall(r'"balance":"(.*?)"', response)[0])

        return balance