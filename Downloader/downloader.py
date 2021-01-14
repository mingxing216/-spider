# -*- coding:utf-8 -*-

"""
下载器
"""

from Utils.timers import Timer
import requests
from requests import adapters
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout
from requests.exceptions import ReadTimeout


def _error(func):
    def wrapper(self, *args, **kwargs):
        try:
            data = func(self, *args, **kwargs)
            if data.status_code in [200, 206]:
                return {'code': 0, 'data': data, 'status': data.status_code, 'message': 'OK'}

            else:
                return {'code': 1, 'data': data, 'status': data.status_code, 'message': 'OK'}

        except (ConnectTimeout, ReadTimeout) as e:
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except ConnectionError as e:
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except Exception as e:
            return {'code': 2, 'data': None, 'status': None, 'message': e}

    return wrapper


class BaseDownloader(object):
    def __init__(self, logging, stream, timeout):
        self.logger = logging
        self.timeout = timeout
        self.stream = stream
        self.timer = Timer()

    @_error
    def get(self, url, session=None, headers=None, data=None, proxies=None, cookies=None):
        self.logger.info('downloader | GET 请求')
        if session is not None:
            # adapters.DEFAULT_RETRIES = 5  # 增加重连次数
            session.keep_alive = False  # 关闭多余连接
            r = session.get(url=url, headers=headers, params=data, cookies=cookies, proxies=proxies,
                            stream=self.stream, timeout=self.timeout)
        else:
            r = requests.get(url=url, headers=headers, params=data, cookies=cookies, proxies=proxies,
                             stream=self.stream, timeout=self.timeout)
        r.close()
        return r

    @_error
    def post(self, url, session=None, headers=None, data=None, proxies=None, cookies=None):
        self.logger.info('downloader | POST 请求')
        if session is not None:
            # adapters.DEFAULT_RETRIES = 5  # 增加重连次数
            # s = requests.session()
            session.keep_alive = False  # 关闭多余连接
            r = session.post(url=url, headers=headers, data=data, proxies=proxies, cookies=cookies,
                             stream=self.stream, timeout=self.timeout)
        else:
            r = requests.post(url=url, headers=headers, data=data, proxies=proxies, cookies=cookies,
                              stream=self.stream, timeout=self.timeout)
        r.close()
        return r

    def begin(self, url, session=None, headers=None, data=None, proxies=None, cookies=None, method='GET'):
        assert method.upper() == 'GET' or method.upper() == 'POST'
        self.logger.info('downloader | 真正开始请求')
        self.timer.start()
        if method.upper() == 'GET':
            resp_data = self.get(url=url, session=session, headers=headers, data=data,
                                 cookies=cookies, proxies=proxies)
            # print(headers)

        elif method.upper() == 'POST':
            resp_data = self.post(url=url, session=session, headers=headers, data=data,
                                  cookies=cookies, proxies=proxies)
        else:
            self.logger.error('downloader | request method error: {}'.format(method))
            return

        if resp_data['code'] == 0 or resp_data['code'] == 1:
            self.logger.info(
                "downloader | request for url: {} | use time: {} | code: {} | status: {} | length: {} | method: {} | "
                "message: {} | data: {} | proxy: {}".format(url, self.timer.use_time(), resp_data['code'],
                                                            resp_data['status'],
                                                            resp_data['data'].headers.get('Content-Length'),
                                                            method, resp_data['message'], data, proxies))
        else:
            self.logger.info(
                "downloader | request for url: {} | use time: {} | code: {} | status: {} | method: {} | message: {} | "
                "data: {} | proxy: {}".format(url, self.timer.use_time(), resp_data["code"], resp_data['status'],
                                              method, resp_data['message'], data, proxies))

        return resp_data
