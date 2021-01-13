# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import time
import requests
import random

from Downloader import downloader
from Utils import user_agent_u, proxy_pool, user_pool, timers
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader.BaseDownloader):
    def __init__(self, logging, stream, timeout, proxy_type, proxy_country, proxy_city, cookie_obj=None):
        super(Downloader, self).__init__(logging=logging, stream=stream, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy_pool.ProxyUtils(logger=logging, mode=proxy_type, country=proxy_country, city=proxy_city)
        self.cookie_obj = cookie_obj
        self.timer = timers.Timer()

    def get_resp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None, user=None):
        self.logger.info('downloader start')
        self.timer.start()
        ret = self._get_resp(url, method, s, data, cookies, referer, ranges, user)
        if not ret:
            self.logger.info('downloader end | 下载失败 | use time: {}'.format(self.timer.use_time()))
            return

        if ret['code'] == 2:
            msg = 'downloader end | 下载失败, 页面响应失败, msg: {} | use time: {}'.format(ret['message'], self.timer.use_time())
            self.logger.error(msg)
            return

        if ret['code'] == 1:
            msg = 'downloader end | 下载失败, 页面响应状态码错误, status: {} | use time: {}'.format(ret['status'], self.timer.use_time())
            self.logger.error(msg)
            return

        self.logger.info('downloader end | 下载成功 | use time: {}'.format(self.timer.use_time()))
        return ret['data']

    def _get_resp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None, user=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            # 设置请求头
            headers = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                # 'Content-Type': 'application/json',
                'Referer': referer,
                'Range': ranges,
                # 'Cookie': 'ASP.NET_SessionId=32nrqfxmdq0r5xcs05eac55d; skybug=46c629a8306c41bd731afe1b03760367; usercssn=UserID=376906&allcheck=732715F2D8B151F6113B09AD01A0352A',
                # 'Connection': 'close',
                # 'Host': 'www.nssd.org',
                'User-Agent': user_agent_u.get_ua()
            }

            # cookie使用次数+1
            if self.cookie_obj is not None and user is not None:
                self.cookie_obj.inc_cookie(user)

            # 设置proxy
            proxies = None
            ip = None
            if self.proxy_type:
                ip = self.proxy_obj.get_proxy()
                if ip:
                    proxies = {'http': 'http://' + ip,
                               'https': 'https://' + ip}
                else:
                    return

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)

            # 返回值中添加IP信息
            down_data['proxy_ip'] = ip
            # 判断
            if down_data['code'] == 0:
                # # 代理权重设最大
                # self.proxy_obj.max_proxy(ip)
                return down_data

            if down_data['code'] == 1:
                # # 代理权重减1
                # self.proxy_obj.dec_proxy(ip)
                if down_data['status'] == 404:
                    return down_data
                else:
                    if stat_count > 3:
                       return down_data
                    else:
                        stat_count += 1
                        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                        continue

            if down_data['code'] == 2:
                # # 代理权重减1
                # self.proxy_obj.dec_proxy(ip)
                if err_count > 3:
                    return down_data
                else:
                    err_count += 1
                    time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                    continue
