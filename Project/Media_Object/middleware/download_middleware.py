# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class Downloader(downloader.BaseDownloaderMiddleware):

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self._startDownload(param=param)





















