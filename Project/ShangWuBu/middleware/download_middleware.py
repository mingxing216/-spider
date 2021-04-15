# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader_bofore
from Utils import user_agent_u
from ProxyPool.ProxyClient import proxy_client
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader_bofore.Downloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy_client.ProxyUtils(logger=logging, mode=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置请求头
            headers = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                'Host': 'policy.mofcom.gov.cn',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                proxies = self.proxy_obj.getProxy()

            # # 设置请求开始时间
            # start_time = time.time()

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)

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




