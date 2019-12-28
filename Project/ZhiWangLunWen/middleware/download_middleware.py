# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
import re
import time
import requests
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u
from Utils import proxy
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                # 'Host': 'navi.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            if self.proxy_type:
                param['proxies'] = self.proxy_obj.getProxy()
            else:
                param['proxies'] = None

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
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
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue


class QiKanLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(QiKanLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                              timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)

    def getIndexHtml(self, url, data=None):
        param = {'url': url}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'productcode': 'CJFD',
            'index': 1
        }

        return self.__judge_verify(param=param)


class HuiYiLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(HuiYiLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                              timeout=timeout,
                                                              proxy_type=proxy_type,
                                                              proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class XueWeiLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(XueWeiLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class HuiYiLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(HuiYiLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class XueWeiLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(XueWeiLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class HuiYiLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(HuiYiLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class XueWeiLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(XueWeiLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_JiGouDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_JiGouDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_ZuoZheDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_ZuoZheDataDownloader, self).__init__(logging=logging,
                                                                 timeout=timeout,
                                                                 proxy_type=proxy_type,
                                                                 proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_HuiYiDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_HuiYiDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200 and len(response.text) > 0:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_QiKanDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_QiKanDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200 and len(response.text) > 0:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_WenJiDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_WenJiDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200 and len(response.text) > 0:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


# class Downloader(downloader.BaseDownloaderMiddleware):
#     def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
#         super(Downloader, self).__init__(logging=logging,
#                                          timeout=timeout,
#                                          retry=retry,
#                                          update_proxy_frequency=update_proxy_frequency,
#                                          proxy_type=proxy_type,
#                                          proxy_country=proxy_country)
#
#     def getResp(self, url, mode, data=None):
#         param = {'url': url}
#
#         # 设置请求方式：GET或POST
#         param['mode'] = mode
#         # 设置请求头
#         param['headers'] = {
#             'User-Agent': user_agent_u.get_ua()
#         }
#         # 设置post参数
#         param['data'] = data
#
#         self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
#         return self._startDownload(param=param)
