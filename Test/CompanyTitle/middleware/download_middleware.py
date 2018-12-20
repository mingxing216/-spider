# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agents
from Utils import proxy_utils
from Utils import create_ua_utils

class Download_58TongCheng(object):
    def __init__(self):
        # 通用请求头
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'User-Agent': create_ua_utils.get_ua()
        }

    # 获取响应【GET通用】
    def getResp(self, logging, redis_client, url):
        for i in range(3):
            # 获取代理IP
            proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
            if proxies is None:
                continue

            # logging.info('当前代理IP: {}'.format(proxies['http']))

            for down_num in range(2):
                # 获取入口页html响应
                resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
                if resp is None:
                    logging.error('入口页HTML响应获取失败')
                    continue

                return resp

            proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
            continue

        return None

    # 获取首页响应
    def getIndexResp(self, logging, url):
        for down_num in range(2):
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers)
            if resp is None:
                logging.error('入口页HTML响应获取失败')
                continue

            return resp

# class Download_Middleware():
#     def __init__(self, logging):
#         self.logging = logging
#
#
#     def demo(self, **kwargs):
#         '''
#         获取响应【demo函数, 仅供参考】
#         :param kwargs: 主要接收参数： redis_client, url, logging
#         :return: 响应内容
#         '''
#         url = kwargs['url']
#         headers = {
#             'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
#         }
#         downloading = downloader.Downloads(headers=headers, logging=self.logging)
#         resp = downloading.newGetRespForGet(url=url)
#
#         return resp





