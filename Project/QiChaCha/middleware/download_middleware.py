# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import proxy_utils

# 基于登录的下载
class Download(object):
    def __init__(self, cookies, user_agent):
        self.cookie = cookies
        self.user_agent = user_agent
        # 通用请求头
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'cookie': self.cookie,
            'referer': 'https://www.qichacha.com',
            'user-agent': self.user_agent
        }

    # 获取响应【通用】GET
    def getResp(self, logging, redis_client, url):
        for i in range(3):
            # 获取代理IP
            proxies = proxy_utils.getProxy(redis_client=redis_client, logging=logging)
            if proxies is None:
                continue

            for down_num in range(2):
                logging.info('发起请求第 {} 次: {}'.format(down_num + 1, url))
                # 获取入口页html响应
                resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
                if resp is None:
                    logging.error('请求失败: {}'.format(url))
                    continue

                logging.info('请求成功: {}'.format(url))
                return resp

            logging.info('删除当前代理: {}'.format(proxies))
            proxy_utils.delProxy(redis_client=redis_client, proxies=proxies)
            logging.info('开始第 {} 次获取代理'.format(i + 2))

        logging.error('重复请求次数已达到最大值。')
        return None

    # 获取当前页响应
    def getIndustryResp(self, logging, redis_client, url):
        for i in range(3):
            # 获取代理IP
            proxies = proxy_utils.getLangProxy(redis_client=redis_client, logging=logging)
            if proxies is None:
                continue

            for down_num in range(2):
                logging.info('发起请求第 {} 次: {}'.format(down_num + 1, url))
                # 获取入口页html响应
                resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
                if resp is None:
                    logging.error('请求失败: {}'.format(url))
                    continue

                logging.info('请求成功: {}'.format(url))
                return resp

            logging.info('开始第 {} 次获取代理'.format(i + 2))

        logging.error('重复请求次数已达到最大值。')
        return None

    # 获取机构主页响应
    def getJiGouHtml(self, logging, url, proxies):
        for down_num in range(2):
            logging.info('发起请求第 {} 次: {}'.format(down_num + 1, url))
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
            if resp is None:
                logging.error('请求失败: {}'.format(url))
                continue
            else:
                logging.info('请求成功: {}'.format(url))
                return resp

        return None


