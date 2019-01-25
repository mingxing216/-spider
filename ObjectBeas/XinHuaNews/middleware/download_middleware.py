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

# Get
def _getResponseForGet(logging, redis_client, url, headers, cookies=None):
    for i in range(3):
        # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
        if proxies is None:
            continue

        # logging.info('当前代理IP: {}'.format(proxies['http']))

        for down_num in range(2):
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=headers, proxies=proxies, cookies=cookies)
            if resp is None:
                logging.error('入口页HTML响应获取失败')
                continue

            return resp

        proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)

    return None

# Post
def _getResponseForPost():
    pass


# 获取响应数据
def getResponse(logging, redis_client, url):
    headers = {
        'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
    }
    resp = _getResponseForGet(logging=logging, redis_client=redis_client, url=url, headers=headers)

    return resp


# 获取思客页响应
def getSiKeResp(self, redis_client, url, data):
    headers = {
        'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
    }
    downloading = downloader.Downloads(headers=headers, logging=self.logging)
    for i in range(2):
        # # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=self.logging)
        # proxies = proxy_utils.getABuYunProxy()

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
def down_img(logging, redis_client, url):
    headers = {
        'User-Agent': random.sample(user_agents.ua_for_mobile, 1)[0]
    }

    for i in range(3):
        # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
        if proxies is None:
            continue

        # logging.info('当前代理IP: {}'.format(proxies['http']))
        for down_num in range(2):
            resp = downloader.downMedia(logging=logging, url=url, headers=headers, proxies=proxies)
            if resp is None:
                logging.error('流媒体内容获取失败， 重试: {}'.format(url))
                continue

            return resp

        proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)

    return None








