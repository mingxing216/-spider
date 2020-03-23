# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader_mod
from Utils import user_agent_u


class Downloader(downloader_mod.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(Downloader, self).__init__(logging=logging,
                                         timeout=timeout,
                                         proxy_type=proxy_type,
                                         proxy_country=proxy_country)

    def getResp(self, url, mode, data=None, cookies=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua(),
        }
        # 设置post参数
        param['data'] = data
        # 设置cookies
        param['cookies'] = cookies

        return self._startDownload(param=param)
