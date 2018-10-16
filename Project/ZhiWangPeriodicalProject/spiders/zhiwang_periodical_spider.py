# -*-coding:utf-8-*-

'''
知网期刊爬虫
'''
import sys
import os
import random
import time
import requests
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from utils import user_agents
from utils import redis_dbutils
from log import log

class SpiderMain(object):
    def __init__(self):
        logname = 'zhiwang_periodical'
        self.logging = log.ILog(logname)
        self.headers = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
        }

    def getProxy(self):
        '''
        随机获取代理IP
        :return: 代理IP
        '''
        for i in range(10):
            proxydata = redis_dbutils.srandmember(settings.REDIS_PROXY_KEY, 1)
            if proxydata:
                proxy = proxydata[0]
                # proxies = {
                #     'http': '{}'.format('http://' + proxy),
                #     'https': '{}'.format('https://' + proxy)
                # }
                proxies = {
                    'http': '{}'.format(proxy),
                    'https': '{}'.format(proxy)
                }

                return proxies
            else:
                time.sleep(1)
                continue


    def delProxy(self, proxies):
        '''
        删除指定代理
        :param proxies: 当前代理
        '''
        proxy = proxies['http']
        redis_dbutils.srem(settings.REDIS_PROXY_KEY, proxy)

    def getRespForGet(self, url):
        # get
        for i in range(10):
            proxies = self.getProxy()
            try:
                resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=10)
                if resp.status_code == 200:
                    response = resp.content.decode('utf-8')
                    return response

                else:
                    self.logging.error('Request fails')
                    time.sleep(1)
                    continue

            except ConnectTimeout and ReadTimeout:
                self.logging.error('Connect Timeout')
                self.delProxy(proxies)
                time.sleep(1)
                continue

            except ConnectionError:
                self.logging.error('Proxy ConnectionError！！！')
                self.delProxy(proxies)
                time.sleep(1)
                continue


    def getRespForPost(self, url, data):
        # post
        for i in range(10):
            proxies = self.getProxy()
            try:
                resp = requests.post(url=url, data=data, headers=self.headers, proxies=proxies, timeout=10)
                if resp.status_code == 200:
                    response = resp.content.decode('utf-8')
                    return response

                else:
                    self.logging.error('Request fails')
                    time.sleep(1)
                    continue

            except ConnectTimeout and ReadTimeout:
                self.logging.error('Connect Timeout')
                self.delProxy(proxies)
                time.sleep(1)
                continue

            except ConnectionError as e:
                print(e)
                self.logging.error('Proxy ConnectionError！！！')
                self.delProxy(proxies)
                time.sleep(1)
                continue




if __name__ == '__main__':
    main = SpiderMain()
    print(main.getRespForGet('https://ip.cn/'))
    # main.getRespForGet('http://www.baidu.com')
