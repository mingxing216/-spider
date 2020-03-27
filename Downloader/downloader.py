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


def _error(func):
    def wrapper(self, *args, **kwargs):
        try:
            data = func(self, *args, **kwargs)
            if data.status_code == 200:
                return {'code': 0, 'data': data, 'status': data.status_code, 'message': 'OK'}

            else:
                return {'code': 1, 'data': None, 'status': data.status_code, 'message': 'OK'}

        except ConnectTimeout or ReadTimeout as e:
            # self.logging.error("Downloader" + " | " + "request timeout: {}s".format(kwargs['timeout']) + " | "
            #                         + kwargs['url'])
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except ConnectionError as e:
            # self.logging.error("Downloader" + " | " + "connection error" + " | " + kwargs['url'] + " | " + str(e))
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except Exception as e:
            # self.logging.error("Downloader" + " | " + "unknown error" + " | " + kwargs['url'] + " | " + str(e))
            return {'code': 2, 'data': None, 'status': None, 'message': e}

    return wrapper


class Downloader(object):
    def __init__(self, logging, timeout):
        self.logging = logging
        self.timeout = timeout

    @_error
    def fetch(self, url, method, session=None, headers=None, data=None, proxies=None, cookies=None, timeout=None):
        assert method.upper() == 'GET' or method.upper() == 'POST'

        if method.upper() == 'GET':
            if session:
                requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
                # s = requests.session()
                session.keep_alive = False  # 关闭多余连接
                # start_time = float(time.time())
                r = session.get(url=url, headers=headers, params=data, cookies=cookies, proxies=proxies, timeout=timeout)
                # end_time = float(time.time())
                # print(round(end_time - start_time, 4))
                # print(r.elapsed.total_seconds())
            else:
                r = requests.get(url=url, headers=headers, params=data, cookies=cookies, proxies=proxies, timeout=timeout)

            return r

        if method.upper() == 'POST':
            if session:
                requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
                # s = requests.session()
                session.keep_alive = False  # 关闭多余连接
                r = session.post(url=url, headers=headers, data=data, proxies=proxies, cookies=cookies, timeout=timeout)
            else:
                r = requests.post(url=url, headers=headers, data=data, proxies=proxies, cookies=cookies, timeout=timeout)

            return r
