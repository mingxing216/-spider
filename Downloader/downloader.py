# -*-coding:utf-8-*-

'''
下载器
'''

import sys
import os
import time
import requests
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from Utils import redispool_utils

class Downloads(object):
    def __init__(self, headers, logging):
        self.headers = headers
        self.logging = logging

    def newGetRespForGet(self, url, proxies=None, cookies=None):
        '''
        requests get请求下载器 
        :param url: url
        :param proxies: 代理IP
        :return: 响应结果
        '''
        try:
            resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=20, cookies=cookies)
            if resp.status_code == 200:
                response = resp.content.decode('utf-8')
                resp.close()
                return response

            else:
                self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                time.sleep(1)

                return None

        except ConnectTimeout or ReadTimeout:
            self.logging.error('Connect Timeout')
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except ConnectionError as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except Exception as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

    def newGetRespForPost(self, url, data, proxies=None, cookies=None):
        try:
            resp = requests.post(url=url, data=data, headers=self.headers, proxies=proxies, timeout=20, cookies=cookies)
            if resp.status_code == 200:
                response = resp.content.decode('utf-8')
                resp.close()
                return response

            else:
                self.logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                time.sleep(1)

                return None

        except ConnectTimeout or ReadTimeout:
            self.logging.error('Connect Timeout')
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except ConnectionError as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except Exception as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

    # 下载流媒体
    def downMedia(self, url, proxies=None):
        try:
            resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=20)
            if resp.status_code == 200:
                response = resp.content
                resp.close()
                return response

            else:
                self.logging.error('HTTP异常返回码： {}, 异常url: {}'.format(resp.status_code, url))
                time.sleep(1)

                return None

        except ConnectTimeout or ReadTimeout:
            self.logging.error('Connect Timeout')
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except ConnectionError as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None

        except Exception as e:
            self.logging.error(e)
            # if (i + 1) % 2 == 0:
            #     self.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            return None




















































































































































































































































    # 以下功能为历史功能， 有项目在使用， 但不再维护
    def getProxy(self, redis_client, logging):
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
                logging.error('代理池代理获取失败')
                time.sleep(1)
                continue

    def getLongProxy(self, redis_client, logging):
        '''
        随机获取代理IP
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

    def delProxy(self, redis_client, proxies):
        '''
        删除指定代理
        :param proxies: 当前代理
        '''
        proxy = proxies['http']
        redispool_utils.srem(redis_client=redis_client, key=settings.REDIS_PROXY_KEY, value=proxy)

    def getRespForGet(self, redis_client, url, logging):
        # get
        for i in range(20):
            proxies = self.getProxy(redis_client, logging)
            if proxies:
                try:
                    resp = requests.get(url=url, headers=self.headers, proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        response = resp.content.decode('utf-8')
                        resp.close()
                        return response

                    else:
                        logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                        time.sleep(1)

                        continue

                except ConnectTimeout or ReadTimeout:
                    logging.error('Connect Timeout')
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except ConnectionError as e:
                    logging.error(e)
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except Exception as e:
                    logging.error(e)
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

            else:
                logging.error('未获取到代理IP')

                continue

    def getRespForPost(self, redis_client, url, data, logging):
        # post
        for i in range(20):
            proxies = self.getProxy(redis_client, logging)
            if proxies:
                try:
                    resp = requests.post(url=url, data=data, headers=self.headers, proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        response = resp.content.decode('utf-8')
                        resp.close()
                        return response

                    else:
                        logging.error('HTTP异常返回码： {}'.format(resp.status_code))
                        time.sleep(1)

                        continue

                except ConnectTimeout or ReadTimeout:
                    logging.error('Connect Timeout')
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except ConnectionError as e:
                    logging.error(e)
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

                except Exception as e:
                    logging.error(e)
                    if (i + 1) % 2 == 0:
                        self.delProxy(redis_client=redis_client, proxies=proxies)
                    time.sleep(0.2)
                    continue

            else:
                logging.error('未获取到代理IP')
                continue

