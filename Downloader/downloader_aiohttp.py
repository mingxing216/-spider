# -*-coding:utf-8-*-

'''
下载器
'''

import sys
import os
import requests
import time
import json
import asyncio
import aiohttp
import traceback

sys.path.append(os.path.dirname(__file__) + os.sep + "../")


class Downloader(object):
    def __init__(self, logging, timeout):
        self.logging = logging
        self.timeout = timeout

    async def fetch(self, session, url, method, headers=None, data=None, proxies=None, cookies=None, timeout=None):
        '''
        基于aiohttp的下载器
        :param url: 目标网址 string
        :param method: 请求方法 GET/POST
        :param headers: 请求头 dict
        :param proxies: 代理IP http://ip:port
        :param timeout: 请求超时时间 int
        :param cookies: cookie
        :param body: post请求参数 dict
        :return: resp
        '''
        assert method.upper() == 'GET' or method.upper() == 'POST'

        if method.upper() == 'GET':
            async with session.get(url=url, headers=headers, data=data, proxy=proxies, timeout=timeout,
                                   cookies=cookies, verify_ssl=False) as resp:

                resp_data =  {
                        'url': str(resp.url),  # url
                        'status': resp.status,  # 响应状态码
                        'headers': resp.headers,  # 响应头
                        'text': await resp.text(),  # 文本格式响应内容
                        # 'json': await resp.json(),  # json格式响应内容
                        # 'read': await resp.read(),  # 文本格式二进制响应内容
                        'content_length': resp.content_length  # 响应长度
                        }

                return resp_data

        if method.upper() == 'POST':
            async with session.post(url=url, headers=headers, proxy=proxies, timeout=timeout, data=data,
                                    cookies=cookies, verify_ssl=False) as resp:
                resp_data = {
                    'url': str(resp.url),  # url
                    'status': resp.status,  # 响应状态码
                    'headers': resp.headers,  # 响应头
                    'text': await resp.text(),  # 文本格式响应内容
                    # 'json': await resp.json(),  # json格式响应内容
                    # 'read': await resp.read(),  # 文本格式二进制响应内容
                    'content_length': resp.content_length  # 响应长度
                }

                return resp_data


    async def begin(self, url, session=None, headers=None, data=None, proxies=None, cookies=None, method='GET'):
        start_time = time.time()
        try:
            resp = await self.fetch(url=url, session=session, headers=headers, data=data,
                                   cookies=cookies, proxies=proxies,
                                   method=method.upper(), timeout=self.timeout)

            self.logging.info(
                "request for url: {} | status: {} | method: {} | message: OK | data: {} | proxy: {} | use time: {}".format(
                    url, resp['status'], method, data, proxies, '%.2fs' % (time.time() - start_time)))

            return resp

        except Exception as e:
            self.logging.info(
                "request for url: {} | status: {} | method: {} | message: {} | data: {} | proxy: {} | use time: {}".format(
                    url, None, method, e, data, proxies, '%.2fs' % (time.time() - start_time)))

            return






