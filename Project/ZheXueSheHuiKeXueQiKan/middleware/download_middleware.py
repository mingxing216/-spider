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
    def __init__(self, logging, stream, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, stream=stream, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        start_time = time.time()
        self.logging.info('开始下载')
        ret = self._getResp(url, method, s, data, cookies, referer, ranges)
        if ret:
            self.logging.info('handle | 下载成功 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 下载失败 | use time: {}s'.format('%.3f' % (time.time() - start_time)))

        self.logging.info('结束下载')
        return ret

    def _getResp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            start_time = time.time()
            # 设置请求头
            headers = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                # 'Content-Type': 'application/json',
                'Referer': referer,
                'Range': ranges,
                # 'Cookie': 'UM_distinctid=1725404ab3d386-0a7cbcacff1eb9-1b386256-13c680-1725404ab3e401; wdcid=6a8ae96755d6ff1e; ASP.NET_SessionId=hczy5jhvk2i0bd3oalpolcre; skybug=40b876da4f8f0d6018497643554d75cc; Hm_lvt_e5019afb8f1df701fe12ca6988a487e5=1596789311,1597044690,1597130145,1597733364; CNZZDATA5545901=cnzz_eid%3D6527406-1594800783-%26ntime%3D1597825840; wdses=4ca1f4fc5f6387a6; CNZZDATA5943370=cnzz_eid%3D1686962856-1594802077-%26ntime%3D1597827602; UserViewPaperHistoryCookie=ViewHistoryList=&ViewHistoryList=7001626186&ViewHistoryList=7102130067&ViewHistoryList=7102130070&ViewHistoryList=7102130074&ViewHistoryList=7102130068&ViewHistoryList=7101674224&ViewHistoryList=67848267504849568349484851&ViewHistoryList=67848267504849568349485148&ViewHistoryList=675603050&ViewHistoryList=67848267504849574849484849&ViewHistoryList=1003219126&ViewHistoryList=7101093640; usercssn=UserID=358042&allcheck=F17C0FFB8394961B4A2CE0CA5760D699; Hm_lpvt_e5019afb8f1df701fe12ca6988a487e5=1597828714; wdlast=1597828714',
                # 'Connection': 'close',
                # 'Host': 'http://www.chinabgao.com/',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                sta = time.time()
                ip = self.proxy_obj.get_proxy()
                proxies = {'http': 'http://' + ip,
                           'https': 'https://' + ip}
                self.logging.info('handle | 获取代理IP成功 | use time: {}s'.format('%.3f' % (time.time() - sta)))

            # # 设置请求开始时间
            # start_time = time.time()

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)
            self.logging.info("handle | request for url: {} | use time: {} | code: {} | status: {} | mode: {}".format(url, '%.3fs' % (time.time() - start_time), down_data['code'], down_data['status'], method))

            if down_data['code'] == 0:
                # 设置代理最大权重
                max_time = time.time()
                max = self.proxy_obj.max_proxy(ip)
                self.logging.info('handle | 设置代理IP最大权重 | use time: {}s'.format('%.3f' % (time.time() - max_time)))
                # self.logging.info('请求成功: {} | 用时: {}秒'.format(url, '%.2f' %(time.time() - start_time)))
                return down_data['data']

            if down_data['code'] == 1:
                # 代理权重减1
                dec_time = time.time()
                dec = self.proxy_obj.dec_proxy(ip)
                self.logging.info('handle | 代理IP权重减1 | use time: {}s'.format('%.3f' % (time.time() - dec_time)))
                if down_data['status'] == 404:
                    return
                else:
                    if stat_count >= 5:
                        return
                    else:
                        stat_count += 1
                        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                        continue

            if down_data['code'] == 2:
                # 代理权重减1
                dec_time = time.time()
                dec = self.proxy_obj.dec_proxy(ip)
                self.logging.info('handle | 代理IP权重减1 | use time: {}s'.format('%.3f' % (time.time() - dec_time)))
                # self.logging.error('请求失败: {} | 错误信息: {} | 用时: {}秒'.format(url, down_data['message'], '%.2f' %(time.time() - start_time)))
                if err_count >= 5:
                    return
                else:
                    err_count += 1
                    time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
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



