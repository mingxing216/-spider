# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(Downloader, self).__init__(logging=logging,
                                         timeout=timeout,
                                         proxy_type=proxy_type,
                                         proxy_country=proxy_country)

    # 网页正常度检测机制
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if '您的IP访问过于频繁，请输入验证码后继续使用' in response.text:
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
