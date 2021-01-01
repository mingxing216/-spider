# -*- coding:utf-8 -*-

import telnetlib
import requests


# 测试代理是否有效
# 来源：https://www.cnblogs.com/hankleo/p/11771682.html


def check_proxy_with_request(ip, port):
    # noinspection PyBroadException
    try:
        # 代理IP地址（高匿）
        proxy = {
            'http': 'http://{}:{}'.format(ip, port),
            'https': 'https://{}:{}'.format(ip, port)
        }
        head = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/50.0.2661.102 Safari/537.36',
            'Connection': 'keep-alive'}
        # http://icanhazip.com会返回当前的IP地址
        p = requests.get('http://icanhazip.com/', headers=head, proxies=proxy)
        if p.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False


async def check_proxy_with_aio(ip, port, session):
    # noinspection PyBroadException
    try:
        proxy = 'http://{}:{}'.format(ip, port)
        head = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/50.0.2661.102 Safari/537.36',
            'Connection': 'keep-alive'}
        r = await session.get('http://icanhazip.com/', headers=head, proxy=proxy)
        if r.status == 200:
            return True
        else:
            return False
    except Exception:
        return False


# 方式二: Telnet方法
def check_proxy_with_telnet(ip, port):
    # noinspection PyBroadException
    try:
        telnetlib.Telnet(ip, port, timeout=2)
        return True
    except Exception:
        return False
