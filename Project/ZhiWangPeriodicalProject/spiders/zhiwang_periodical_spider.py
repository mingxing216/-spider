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
from utils import redispool_utils
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

    def getProxy(self, redis_client):
        '''
        随机获取代理IP
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
                self.logging.error('代理池代理获取失败')
                time.sleep(1)
                continue

    def delProxy(self, redis_client, proxies):
        '''
        删除指定代理
        :param proxies: 当前代理
        '''
        proxy = proxies['http']
        redispool_utils.srem(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, value=proxy)

    def getRespForGet(self, redis_client, url):
        # get
        # while True:
        for i in range(20):
            proxies = self.getProxy(redis_client)
            if proxies:
                try:
                    resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        response = resp.content.decode('utf-8')

                        return response

                    else:
                        self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                        time.sleep(1)

                        continue

                # except ConnectTimeout and ReadTimeout:
                #     self.logging.error('Connect Timeout')
                #     self.delProxy(redis_client=redis_client, proxies=proxies)
                #     time.sleep(0.2)
                #
                #     continue
                #
                # except ConnectionError:
                #     self.logging.error('Proxy ConnectionError！！！')
                #     self.delProxy(redis_client=redis_client, proxies=proxies)
                #     time.sleep(0.2)
                #
                #     continue
                except ConnectTimeout and ReadTimeout:
                    self.logging.error('Connect Timeout')
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except ConnectionError as e:
                    self.logging.error(e)
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

            else:
                self.logging.error('未获取到代理IP')

                continue

    def getRespForPost(self, redis_client, url, data):
        # post
        # while True:
        for i in range(20):
            proxies = self.getProxy(redis_client)
            if proxies:
                try:
                    resp = requests.post(url=url, data=data, headers=self.headers, proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        response = resp.content.decode('utf-8')

                        return response

                    else:
                        self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                        time.sleep(1)

                        continue

                # except ConnectTimeout and ReadTimeout:
                #     self.logging.error('Connect Timeout')
                #     self.delProxy(redis_client=redis_client, proxies=proxies)
                #     time.sleep(0.2)
                #
                #     continue
                #
                # except ConnectionError:
                #     self.logging.error('Proxy ConnectionError！！！')
                #     self.delProxy(redis_client=redis_client, proxies=proxies)
                #     time.sleep(0.2)
                #
                #     continue
                except ConnectTimeout and ReadTimeout:
                    self.logging.error('Connect Timeout')
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except ConnectionError:
                    self.logging.error('Proxy ConnectionError！！！')
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

            else:
                self.logging.error('未获取到代理IP')
                continue

if __name__ == '__main__':
    main = SpiderMain()
    print(main.getRespForGet('https://ip.cn/'))
    # main.getRespForGet('http://www.baidu.com')
