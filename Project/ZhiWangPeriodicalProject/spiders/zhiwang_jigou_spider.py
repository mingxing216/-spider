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
from utils import timeutils
from log import log

class SpiderMain(object):
    def __init__(self):
        logname = 'zhiWangJiGou_spider'
        self.logging = log.ILog(logname)
        self.headers = {
            'Host': 'kns.cnki.net',
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
                begin_time = time.time()
                resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=10)
                if resp.status_code == 200:
                    # 代理请求时间
                    out_time = time.time() - begin_time
                    # 当前代理
                    proxy = proxies['http']
                    try:
                        # 响应大小
                        content_length = resp.headers['Content-Length']
                    except:
                        content_length = 0
                    self.logging.info('芝麻代理: {proxy}, 响应时间: {out_time}, 响应大小: {content_length}'
                                      .format(proxy=proxy,
                                              out_time=out_time,
                                              content_length=content_length))

                    response = resp.content.decode('utf-8')


                    return response

                else:
                    self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                    time.sleep(1)
                    continue

            except ConnectTimeout and ReadTimeout:
                self.logging.error('Connect Timeout')
                if (i + 1) % 2 == 0:
                    self.delProxy(proxies)
                time.sleep(0.2)
                continue

            except ConnectionError:
                self.logging.error('Proxy ConnectionError！！！')
                if (i + 1) % 2 == 0:
                    self.delProxy(proxies)
                time.sleep(0.2)
                continue


    def getRespForPost(self, url, data):
        # post
        for i in range(10):
            proxies = self.getProxy()
            try:
                begin_time = timeutils.get_current_millis()
                resp = requests.post(url=url, data=data, headers=self.headers, proxies=proxies, timeout=10)
                if resp.status_code == 200:
                    # 代理请求时间
                    out_time = timeutils.get_current_millis() - begin_time
                    # 当前代理
                    proxy = proxies['http']
                    try:
                        # 响应大小
                        content_length = resp.headers['Content-Length']
                    except:
                        content_length = 0
                    self.logging.info('芝麻代理: {proxy}, 响应时间: {out_time}, 响应大小: {content_length}'
                                      .format(proxy=proxy,
                                              out_time=out_time,
                                              content_length=content_length))

                    response = resp.content.decode('utf-8')

                    return response

                else:
                    self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                    time.sleep(1)
                    continue

            except ConnectTimeout and ReadTimeout:
                self.logging.error('Connect Timeout')
                if (i + 1) % 2 == 0:
                    self.delProxy(proxies)
                time.sleep(0.2)
                continue

            except ConnectionError as e:
                self.logging.error('Proxy ConnectionError！！！')
                if (i + 1) % 2 == 0:
                    self.delProxy(proxies)
                time.sleep(0.2)
                continue




if __name__ == '__main__':
    main = SpiderMain()
    print(main.getRespForGet('https://ip.cn/'))
    # main.getRespForGet('http://www.baidu.com')
