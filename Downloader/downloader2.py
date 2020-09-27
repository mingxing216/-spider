# -*-coding:utf-8-*-

'''
下载器
'''

import time
import sys
import os
import requests
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
from Log import log


def _error(func):
    def wrapper(self, *args, **kwargs):
        try:
            data = func(self, *args, **kwargs)['data']
            if data.status_code == 200:

                return {'status': 0, 'data': data}
            else:
                self.logging.error("Downloader" + " | " + 'response status code is {}'.format(data.status_code) + " | "
                                    + kwargs['url'])

                return {'status': 1, 'data': None}
        except ConnectTimeout or ReadTimeout:
            self.logging.error("Downloader" + " | " + "request timeout: {}s".format(kwargs['timeout']) + " | "
                                    + kwargs['url'])

            return {'status': 2, 'data': None}

        except ConnectionError as e:
            self.logging.error("Downloader" + " | " + "connection error" + " | " + kwargs['url'] + " | "
                                + str(e))

            return {'status': 2, 'data': None}

        except Exception as e:
            self.logging.error("Downloader" + " | " + "unknown error" + " | " + kwargs['url'] + " | "
                                + str(e))

            return {'status': 2, 'data': None}

    return wrapper


class Downloader(object):
    def __init__(self, logging):
        self.logging = logging

    @_error
    def get(self, url: object, headers: object = None, cookies: object = None, timeout: object = None, proxies: object = None) -> object:
        resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=timeout, cookies=cookies)

        return resp

    @_error
    def post(self, url, headers=None, data=None, cookies=None, timeout=None, proxies=None):
        resp = requests.post(url=url, headers=headers, data=data, proxies=proxies, timeout=timeout, cookies=cookies)

        return resp


if __name__ == '__main__':
    log_file_dir = 'demo'  # LOG日志存放路径
    LOGNAME = 'demo'  # LOG名
    LOGGING = log.ILog(log_file_dir, LOGNAME)

    obj = Downloader(logging=LOGGING)
    url = 'http://www.baidu.comm'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    proxies = {
        'http': 'socks5://36.248.147.21:4216',
        'https': 'socks5://36.248.147.21:4216'
    }
    begin_time = time.time()
    resp = obj.get(url=url, headers=headers, timeout=5)

    print(resp)
    print(time.time() - begin_time)

