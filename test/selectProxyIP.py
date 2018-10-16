#-*-coding:utf-8-*-
'''
代理ip测试服务
直接运行本代码， 可查看获取源码内当前使用代理IP是多少
'''
import os
import sys

import requests
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
from Project.ZhiWangPeriodicalProject.services import proxy_service

url = 'https://ip.cn/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
}

proxy_server = proxy_service.ProxyServices()
proxy = proxy_server.srandmemberProxy('proxy', 1)
proxies = {
            'http': '{}'.format(proxy),
            'https': '{}'.format(proxy)
        }

try:
    resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=5, verify=False)
    if resp.status_code is 200:
        print('访问成功')
        print(resp.content.decode('utf8'))
    else:
        print('访问失败')
except ConnectTimeout and ReadTimeout:
    print('访问超时')

except ConnectionError:
    print('代理失效')


