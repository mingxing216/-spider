# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random
import time

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
            proxies = proxy_utils.getHttpsProxy(redis_client=redis_client, logging=logging)
            if proxies is None:
                continue

            for down_num in range(2):
                # logging.info('发起请求第 {} 次: {}'.format(down_num + 1, url))
                # 获取入口页html响应
                resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
                if resp is None:
                    # logging.error('请求失败: {}'.format(url))
                    continue

                # 检查是否出现验证码
                if len(resp) < 200:
                    logging.error('出现验证码')
                    # # logging.info('删除当前代理: {}'.format(proxies))
                    # proxy_utils.delHttpsProxy(redis_client=redis_client, proxies=proxies)
                    # # logging.info('开始第 {} 次获取代理'.format(i + 2))
                    break

                # logging.info('请求成功: {}'.format(url))
                time.sleep(random.randint(40, 60))
                return resp

            # logging.info('删除当前代理: {}'.format(proxies))
            proxy_utils.delHttpsProxy(redis_client=redis_client, proxies=proxies)
            # logging.info('开始第 {} 次获取代理'.format(i + 2))

        # logging.error('重复请求次数已达到最大值。')
        return None

    # 获取响应【通用】GET | ADSL_PROXY
    def getResp_Adsl(self, logging, url):
        while True:
            # 获取代理IP
            proxies = proxy_utils.getAdslProxy(logging=logging)
            if proxies is None:
                logging.error('代理获取失败')
                time.sleep(1)
                continue
            logging.info('已获取adsl代理：{}'.format(proxies))
            break

        # 获取入口页html响应
        resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)

        if resp is None:
            # 标记此代理
            proxy_utils.updateAdslProxy(proxies)

            return {'status': 1}

        if len(resp) < 200:
            logging.error('出现验证码')
            # 标记此代理
            proxy_utils.updateAdslProxy(proxies)

            return {'status': 2}

        return {'status': 0, 'data': resp}


    # 获取机构主页响应
    def getJiGouHtml(self, logging, url, proxies):
        for down_num in range(2):
            # logging.info('发起请求第 {} 次: {}'.format(down_num + 1, url))
            # 获取入口页html响应
            resp = downloader.newGetRespForGet(logging=logging, url=url, headers=self.headers, proxies=proxies)
            if resp is None:
                # logging.error('请求失败: {}'.format(url))
                continue
            else:
                # logging.info('请求成功: {}'.format(url))
                return resp

        return None


