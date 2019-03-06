# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(Downloader, self).__init__(logging=logging,
                                         timeout=timeout,
                                         retry=retry,
                                         update_proxy_frequency=update_proxy_frequency,
                                         proxy_type=proxy_type,
                                         proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

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
        return self._startDownload(param=param)
