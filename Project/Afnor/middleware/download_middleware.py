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


class DownloaderMiddleware(downloader.Downloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(DownloaderMiddleware, self).__init__(logging=logging, timeout=timeout)
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

            # 设置请求头
            if 'token' in url:
                host = 'viewer.afnor.org'
            else:
                host = 'www.boutique.afnor.org'
            headers = {
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                # 'Content-Type':'application/json; charset=UTF-8', # post RequestPayload请求需要
                'Connection': 'close',
                'Host': host,
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                proxies = self.proxy_obj.getProxy()

            down_data = self.fetch(session=s, url=url, method=mode, data=data, headers=headers, proxies=proxies, cookies=cookies)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data']}

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
