# -*-coding:utf-8-*-

'''
下载器
'''

import sys
import os
import requests
import time
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
from settings import DOWNLOAD_DELAY
from Utils import proxy


def _error(func):
    def wrapper(self, *args, **kwargs):
        try:
            data = func(self, *args, **kwargs)
            if data.status_code == 200:
                return {'status': 0, 'data': data, 'code': data.status_code}

            else:
                return {'status': 1, 'data': None, 'code': data.status_code}

        except ConnectTimeout or ReadTimeout:
            # self.logging.error("Downloader" + " | " + "request timeout: {}s".format(kwargs['timeout']) + " | "
            #                         + kwargs['url'])
            return {'status': 2, 'data': None}

        except ConnectionError as e:
            # self.logging.error("Downloader" + " | " + "connection error" + " | " + kwargs['url'] + " | " + str(e))
            return {'status': 2, 'data': None}

        except Exception as e:
            # self.logging.error("Downloader" + " | " + "unknown error" + " | " + kwargs['url'] + " | " + str(e))
            return {'status': 2, 'data': None}

    return wrapper


class BaseDownloaderMiddleware(object):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        self.logging = logging
        self.downloader = Downloader(logging=logging,
                                     proxy_type=proxy_type,
                                     timeout=timeout,
                                     proxy_country=proxy_country)

    def _startDownload(self, param):
        try:
            url = param['url']
        except:
            url = None
        try:
            mode = param['mode'].upper()
        except:
            mode = None
        try:
            headers = param['headers']
        except:
            headers = None
        try:
            data = param['data']
        except:
            data = None
        try:
            cookies = param['cookies']
        except:
            cookies = None

        if not url:
            raise Exception("Please specify URL")

        if not mode:
            raise Exception('Please specify request for GET or POST')

        if mode == 'GET':
            resp = self.downloader.begin(url=url, connect_type='GET', headers=headers, cookies=cookies)
            return resp

        if mode == 'POST':
            resp = self.downloader.begin(url=url, connect_type='POST', headers=headers, data=data, cookies=cookies)
            return resp


class Downloader(object):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        self.logging = logging
        self.timeout = timeout
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country)

    @_error
    def get(self, url, headers, cookies, timeout, proxies):
        return requests.get(url=url, headers=headers, proxies=proxies, timeout=timeout, cookies=cookies)

    @_error
    def post(self, url, headers, data, cookies, timeout, proxies):
        return requests.post(url=url, headers=headers, data=data, proxies=proxies, timeout=timeout, cookies=cookies)

    def start(self, url, headers, data, cookies, timeout, proxies, connect_type):
        time.sleep(int(DOWNLOAD_DELAY))

        if connect_type == 'GET':
            return self.get(url=url, headers=headers, cookies=cookies,
                                 timeout=timeout, proxies=proxies)

        if connect_type == 'POST':
            return self.post(url=url, headers=headers, data=data,
                                  cookies=cookies, timeout=timeout, proxies=proxies)

    def begin(self, url, headers=None, data=None, cookies=None, connect_type='GET'):
        if self.proxy_type is not None:
            # 请求异常时间戳
            err_time = 0
            while 1:
                proxies = self.proxy_obj.getProxy()
                start_time = int(time.time())
                down_data = self.start(url=url, headers=headers, data=data,
                                       cookies=cookies, timeout=self.timeout, proxies=proxies,
                                       connect_type=connect_type.upper())
                end_time = int(time.time())
                self.logging.info("request for url: {} | status: {} | mode: {} | data: {} | proxy: {} | use time: {}".format(
                    url, down_data['status'], connect_type, data, proxies, '{}s'.format(end_time - start_time)
                ))

                if down_data['status'] == 0:
                    return {'status': 0, 'data': down_data['data'], 'proxies': proxies}

                if down_data['status'] == 1:
                    status_code = str(down_data['code'])
                    if status_code != '404':
                        continue
                    else:
                        return {'status': 1, 'data': url}

                if down_data['status'] == 2:
                    '''
                    如果未设置请求异常的时间戳，则现在设置；
                    如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                    {'status': 1}
                    '''
                    if err_time == 0:
                        err_time = int(time.time())
                        continue

                    else:
                        # 获取当前时间戳
                        now = int(time.time())
                        if now - err_time >= 150:
                            return {'status': 1, 'data': url}
                        else:
                            continue

        else:
            down_data = self.start(url=url, headers=headers, data=data,
                                   cookies=cookies, timeout=self.timeout, proxies=None,
                                   connect_type=connect_type.upper())

            if down_data['status'] == 0:
                return {'status': 0, 'data': down_data['data']}

            return {'status': 1, 'url': url}

