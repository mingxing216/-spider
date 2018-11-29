# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agents
from Utils import proxy_utils

class Download_Middleware():
    def __init__(self, logging):
        self.logging = logging

    # 获取响应数据
    def getResponse(self, redis_client, url):
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)

        for i in range(20):
            # 获取代理IP
            proxies = proxy_utils.getProxy(redis_client=redis_client, logging=self.logging)

            for down_num in range(2):
                resp = downloading.newGetRespForGet(url=url, proxies=proxies)
                if resp is None:
                    self.logging.error('首页html获取失败, 重试')
                    continue

                return resp

            proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            continue

    # 获取思客页响应
    def getSiKeResp(self, redis_client, url, data):
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        for i in range(2):
            # 获取代理IP
            proxies = proxy_utils.getProxy(redis_client=redis_client, logging=self.logging)

            for down_num in range(2):
                resp = downloading.newGetRespForPost(url=url, data=data, proxies=proxies)
                if resp is None:
                    self.logging.error('首页html获取失败, 重试')
                    continue

                return resp

            proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            continue

    # 下载图片
    def down_img(self, redis_client, url):
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        for i in range(20):
            # 获取代理IP
            proxies = proxy_utils.getProxy(redis_client=redis_client, logging=self.logging)

            for down_num in range(2):
                resp = downloading.downMedia(url=url, proxies=proxies)
                if resp is None:
                    self.logging.error('流媒体内容获取失败， 重试')
                    continue

                return resp

            proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
            time.sleep(0.2)
            continue


    def demo(self, **kwargs):
        '''
        获取响应【demo函数, 仅供参考】
        :param kwargs: 主要接收参数： redis_client, url, logging
        :return: 响应内容
        '''
        url = kwargs['url']
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForGet(url=url)

        return resp





