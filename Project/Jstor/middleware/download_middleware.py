# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import requests
import random
import asyncio
import aiohttp
import traceback

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

    async def getResp(self, url, method, session=None, data=None, cookies=None, referer=''):
        # 重试次数
        count = 0
        while True:
            # 下载延时
            await asyncio.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

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

            # 设置请求开始时间戳
            start_time = int(time.time())

            # self.logging.info('发送请求: {}'.format(url))
            # 获取响应数据
            try:
                resp = await self.fetch(session=session, url=url, method=method, headers=headers, proxies=proxies, cookies=cookies, data=data)
                # print(resp)
                if resp.get('status') != 200:
                    self.logging.warning('响应码: {}'.format(resp.get('status')))
                    if count > 10:
                        return
                    else:
                        count += 1
                        continue

            except:
                self.logging.error('请求失败: {} | message: {}'.format(url, str(traceback.format_exc())))
                if count > 5:
                    return
                else:
                    count += 1
                    continue

            self.logging.info('请求成功: {} | 耗时: {}s'.format(url, int(time.time()) - start_time))

            return resp
