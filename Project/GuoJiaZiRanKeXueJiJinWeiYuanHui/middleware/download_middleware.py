# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time
import requests
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader_bofore
from Utils import user_agent_u
from ProxyPool.ProxyClient import proxy_client
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, stream, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, stream=stream, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy_client.ProxyPoolClient(logger=logging)

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
                'Content-Type': 'application/json',
                'Referer': referer,
                'Range': ranges,
                # 'Connection': 'close',
                # 'Host': 'http://www.chinabgao.com/',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            ip = None
            if self.proxy_type:
                ip = self.proxy_obj.get_proxy()
                proxies = {'http': 'http://' + ip,
                           'https': 'https://' + ip}

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)
            # self.logging.info("handle | request for url: {} | use time: {} | code: {} | status: {} | method: {}".format(url, '%.3fs' % (time.time() - start_time), down_data['code'], down_data['status'], method))

            if down_data['code'] == 0:
                # 设置代理最大权重
                self.proxy_obj.max_proxy(ip)
                # self.logging.info('请求成功: {} | 用时: {}秒'.format(url, '%.2f' %(time.time() - start_time)))
                return down_data

            if down_data['code'] == 1:
                # 代理权重减1
                self.proxy_obj.dec_proxy(ip)
                if down_data['status'] == 404:
                    return down_data
                else:
                    if stat_count > 3:
                        return
                    else:
                        stat_count += 1
                        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                        continue

            if down_data['code'] == 2:
                # 代理权重减1
                self.proxy_obj.dec_proxy(ip)
                # self.logging.error('请求失败: {} | 错误信息: {} | 用时: {}秒'.format(url, down_data['message'], '%.2f' %(time.time() - start_time)))
                if err_count > 3:
                    return down_data
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
