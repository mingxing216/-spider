# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import proxy_utils
from Utils import create_ua_utils


# 获取响应【通用】
def getResp(logging, redis_client, url):
    headers = {
        'Host': 'c.old.wanfangdata.com.cn',
        'Referer': 'http://old.wanfangdata.com.cn/',
        'User-Agent': create_ua_utils.get_ua()
    }
    for i in range(3):
        # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
        if proxies is None:
            continue

        # logging.info('当前代理IP: {}'.format(proxies['http']))

        for down_num in range(2):
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=headers, proxies=proxies)
            if resp is None:
                logging.error('入口页HTML响应获取失败')
                continue

            return resp

        proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
        continue

    return None

# 获取专利列表页响应
def getPatentClassifyRest(logging, redis_client, url):
    headers = {
        'Host': 's.wanfangdata.com.cn',
        'User-Agent': create_ua_utils.get_ua()
    }
    for i in range(3):
        # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
        if proxies is None:
            continue

        # logging.info('当前代理IP: {}'.format(proxies['http']))

        for down_num in range(2):
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=headers, proxies=proxies)
            if resp is None:
                logging.error('入口页HTML响应获取失败')
                continue

            return resp

        proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
        continue

    return None

# 获取专利主页html
def getPatentHtml(logging, redis_client, url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Host': 'd.old.wanfangdata.com.cn',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': create_ua_utils.get_ua()
    }
    for i in range(3):
        # 获取代理IP
        proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
        if proxies is None:
            continue

        logging.info('当前代理IP: {}'.format(proxies['http']))

        for down_num in range(2):
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=headers, proxies=proxies)
            if resp is None:
                logging.error('入口页HTML响应获取失败')
                continue

            return resp

        proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)

    return None