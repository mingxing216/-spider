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

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u
from Utils import proxy
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        start_time = time.time()
        self.logging.info('开始下载附件')
        ret = self._getResp(url, method, s, data, cookies, referer)
        if ret:
            self.logging.info('request for url: {} | use time: {}s'.format(url, '%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('request for url: {} | use time: {}s'.format(url, '%.3f' % (time.time() - start_time)))

        self.logging.info('结束下载附件')
        return ret

    def _getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            start_time = time.time()

            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置请求头
            headers = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                # 'Content-Type': 'application/json',
                'Referer': referer,
                'Connection': 'close',
                # 'Host': 'http://www.chinabgao.com/',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                ip = self.proxy_obj.get_proxy()
                proxies = {'http': 'http://' + ip,
                           'https': 'https://' + ip}

            # # 设置请求开始时间
            # start_time = time.time()

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)
            self.logging.info(
                "request for url: {} | code: {} | status: {} | mode: {} | use time: {}".format(url, down_data['code'], down_data['status'], method, '%.3fs' % (time.time() - start_time)))

            if down_data['code'] == 0:
                # 设置代理最大权重
                max = self.proxy_obj.max_proxy(ip)
                # self.logging.info('请求成功: {} | 用时: {}秒'.format(url, '%.2f' %(time.time() - start_time)))
                return down_data['data']

            if down_data['code'] == 1:
                # 代理权重减1
                dec = self.proxy_obj.dec_proxy(ip)
                if down_data['status'] == 404:
                    return
                else:
                    if stat_count > 10:
                        return
                    else:
                        stat_count += 1
                        continue

            if down_data['code'] == 2:
                # 代理权重减1
                dec = self.proxy_obj.dec_proxy(ip)
                # self.logging.error('请求失败: {} | 错误信息: {} | 用时: {}秒'.format(url, down_data['message'], '%.2f' %(time.time() - start_time)))
                if err_count > 10:
                    return
                else:
                    err_count += 1
                    continue

    # 创建COOKIE
    def create_cookie(self):
        # url = 'http://kns.cnki.net/kns/request/NaviGroup.aspx?code=A&tpinavigroup=SCPD_FMtpiresult&catalogName=SCPD_IPCCLS&__=Wed%20Nov%2027%202019%2015%3A00%3A02%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
        url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SCPD_FM'
        try:
            resp = self.getResp(url=url, method='GET')
            if resp:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None



