# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class Task_Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(Task_Downloader, self).__init__(logging=logging,
                                              timeout=timeout,
                                              retry=retry,
                                              update_proxy_frequency=update_proxy_frequency,
                                              proxy_type=proxy_type,
                                              proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 网页正常度检测机制
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            # 如果下载异常，重新下载
            if resp['status'] != 0:
                continue

            # 如果下载成功， 并且响应内容不是None, 设置响应结果，否则响应设置None
            if resp['status'] == 0 and resp['data'] is not None:
                response = resp['data']
            else:
                response = None

            # 检测是否遇到验证码
            if response is not None:
                proxies = resp['proxies']
                if '您的IP访问过于频繁，请输入验证码后继续使用' in response.text:
                    self.logging.info('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                else:
                    return response

            # 返回响应内容
            return response

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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class Data_Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(Data_Downloader, self).__init__(logging=logging,
                                              timeout=timeout,
                                              retry=retry,
                                              update_proxy_frequency=update_proxy_frequency,
                                              proxy_type=proxy_type,
                                              proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 网页正常度检测机制
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            # 如果下载异常，重新下载
            if resp['status'] != 0:
                continue

            # 如果下载成功， 并且响应内容不是None, 设置响应结果，否则响应设置None
            if resp['status'] == 0 and resp['data'] is not None:
                response = resp['data']
            else:
                response = None

            # 检测是否遇到验证码
            if response is not None:
                proxies = resp['proxies']
                if '您的IP访问过于频繁，请输入验证码后继续使用' in response.text:
                    self.logging.info('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                else:
                    return response

            # 返回响应内容
            return response

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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)
