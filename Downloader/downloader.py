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
                self.logging.error("Downloader" + " | " + 'response status code is {}'.format(data.status_code) + " | "
                                    + kwargs['url'])
                return {'status': 1, 'data': None, 'code': data.status_code}

        except ConnectTimeout or ReadTimeout:
            self.logging.error("Downloader" + " | " + "request timeout: {}s".format(kwargs['timeout']) + " | "
                                    + kwargs['url'])
            return {'status': 2, 'data': None}

        except ConnectionError as e:
            self.logging.error("Downloader" + " | " + "connection error" + " | " + kwargs['url'] + " | " + str(e))
            return {'status': 2, 'data': None}

        except Exception as e:
            self.logging.error("Downloader" + " | " + "unknown error" + " | " + kwargs['url'] + " | " + str(e))
            return {'status': 2, 'data': None}

    return wrapper


class BaseDownloaderMiddleware(object):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        self.logging = logging
        self.downloader = Downloader(logging=logging,
                                     update_proxy_frequency=update_proxy_frequency,
                                     proxy_type=proxy_type,
                                     timeout=timeout,
                                     retry=retry,
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

        if not url:
            raise Exception("Please specify URL")

        if not mode:
            raise Exception('Please specify request for GET or POST')

        if mode == 'GET':
            resp = self.downloader.begin(url=url, connect_type='GET', headers=headers)
            return resp

        if mode == 'POST':
            resp = self.downloader.begin(url=url, connect_type='POST', headers=headers, data=data)
            return resp


class Downloader(object):
    def __init__(self, logging, update_proxy_frequency, timeout, retry, proxy_type, proxy_country):
        assert isinstance(update_proxy_frequency, int)

        self.logging = logging
        self.timeout = timeout
        self.retry = retry
        self.proxy_type = proxy_type
        self.update_proxy_frequency = update_proxy_frequency
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country)

    @_error
    def get(self, url, headers, cookies, timeout, proxies):
        resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=timeout, cookies=cookies)
        return resp

    @_error
    def post(self, url, headers, data, cookies, timeout, proxies):
        resp = requests.post(url=url, headers=headers, data=data, proxies=proxies, timeout=timeout, cookies=cookies)
        return resp

    def start(self, url, headers, data, cookies, timeout, proxies, connect_type):
        time.sleep(int(DOWNLOAD_DELAY))
        if connect_type == 'GET':
            down_data = self.get(url=url, headers=headers, cookies=cookies,
                                 timeout=timeout, proxies=proxies)
            return down_data

        if connect_type == 'POST':
            down_data = self.post(url=url, headers=headers, data=data,
                                  cookies=cookies, timeout=timeout, proxies=proxies)
            return down_data

    def begin(self, url, headers=None, data=None, cookies=None, connect_type='GET'):
        if self.proxy_type is not None:
            for get_proxy_number in range(int(self.update_proxy_frequency)):
                proxies = self.proxy_obj.getProxy()

                for i in range(self.retry):
                    down_data = self.start(url=url, headers=headers, data=data,
                                           cookies=cookies, timeout=self.timeout, proxies=proxies, connect_type=connect_type.upper())

                    if down_data['status'] == 0:

                        return {'status': 0, 'data': down_data['data'], 'proxies': proxies}

                    if down_data['status'] == 1:
                        status_code = str(down_data['code'])
                        if status_code.startswith('5'):
                            continue
                        else:
                            return {'status': 1}

                    if down_data['status'] == 2:

                        continue

                # 删除代理
                self.proxy_obj.delProxy(proxies)

            return {'status': 1}

        else:
            down_data = self.start(url=url, headers=headers, data=data,
                                   cookies=cookies, timeout=self.timeout, proxies=None, connect_type=connect_type.upper())

            if down_data['status'] == 0:
                return {'status': 0, 'data': down_data['data']}

            return {'status': 1}



