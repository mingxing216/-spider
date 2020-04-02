# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import requests
import random
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

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

    def get_headers(self):
        headers_list = [
            {
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Scheme': 'https',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Cache-Control': 'max-age=0',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Cache-Control': 'max-age=0',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Upgrade-Insecure-Requests': '1',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Cache-Control': 'max-age=0',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            }
        ]

        headers = random.choice(headers_list)
        return headers

    def getResp(self, url, method, session=None, data=None, cookies=None, referer=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            # 下载延时
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置请求头
            headers = {
                # 'authority': 'www.jstor.org',
                'method': 'GET',
                'scheme': 'https',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                # 'accept-language': 'zh-CN,zh;q=0.9',
                # 'accept-encoding': 'gzip, deflate, br',
                # 'sec-fetch-mode': 'navigate',
                'referer': referer,
                'connection': 'close',
                'user-agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                proxies = self.proxy_obj.getProxy()

            # # 设置请求开始时间
            # start_time = time.time()

            # 获取响应
            down_data = self.begin(session=session, url=url, method=method, data=data, headers=headers, proxies=proxies, cookies=cookies)

            # self.logging.info(
            #     "request for url: {} | code: {} | status: {} | method: {} | data: {} | proxy: {}".format(
            #         url, down_data['code'], down_data['status'], method,  data, proxies
            #     ))

            if down_data['code'] == 0:
                # self.logging.info('请求成功: {} | 用时: {}秒'.format(url, '%.2f' %(time.time() - start_time)))
                return down_data['data']

            if down_data['code'] == 1:
                # self.logging.warning('请求内容错误: {} | 响应码: {} | 用时: {}秒'.format(url, down_data['status'], '%.2f' %(time.time() - start_time)))
                if stat_count > 20:
                    return
                else:
                    stat_count += 1
                    continue

            if down_data['code'] == 2:
                # self.logging.error('请求失败: {} | 错误信息: {} | 用时: {}秒'.format(url, down_data['message'], '%.2f' %(time.time() - start_time)))
                if err_count > 10:
                    return
                else:
                    err_count += 1
                    continue

    # 创建COOKIE
    def create_cookie(self):
        url = 'https://www.jstor.org/'
        try:
            resp = self.getResp(url=url, method='GET')
            if resp:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp.cookies)

        except:
            self.logging.error('cookie创建异常')
            return None

