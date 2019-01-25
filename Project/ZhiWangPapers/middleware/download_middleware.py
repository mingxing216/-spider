# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class UrlDownloader(downloader.BaseDownloaderMiddleware):

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                resp = resp['data']
                if len(resp.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp['data']
    
    # 通用下载
    def getResp(self, url, data=None):
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
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))

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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class QiKanDownloader(downloader.BaseDownloaderMiddleware):

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                resp = resp['data']
                if len(resp.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp['data']

    def getResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, data))
        return self.__judge_verify(param=param)
    
    def getImageResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, data))
        resp = self._startDownload(param=param)
        if resp['status'] == 1:
            return None

        return resp['data']

class Downloader(downloader.BaseDownloaderMiddleware):

    def getResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, data))
        return self.startDownload(param=param)























