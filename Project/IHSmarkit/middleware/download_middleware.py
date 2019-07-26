# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
import re
import time
import requests

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u
from Utils import proxy


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        while 1:
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Cache-Control': 'max-age=0',
                # 'Upgrade-Insecure-Requests': '1',
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'accept-encoding': 'gzip, deflate, br',
                # 'Referer': referer,
                'Host': 'global.ihs.com',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param)

            if down_data['status'] == 0:
                return {'status': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['status'] == 1:
                status_code = str(down_data['code'])
                if status_code != '404':
                    continue
                else:
                    return {'status': 1, 'data': url}

            if down_data['status'] == 2:
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
                    if now - err_time >= 90:
                        return {'status': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        url = 'https://www.jstor.org/'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['status'] == 0:
                # print(resp.cookies)
                return requests.utils.dict_from_cookiejar(resp['data'].cookies)
        except:
            self.logging.info('cookie创建异常')
            return None
