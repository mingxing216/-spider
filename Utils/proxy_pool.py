# -*- coding:utf-8 -*-
"""
简介：本文件是框架内部功能文件，除框架开发人员，任何人不可对本文件代码进行任何形式的更改。
     主要负责提供代理池代理增、删、改、查操作接口
开发人：采集部-王勇
开发时间：2019年01月04日
更新人：采集部-张明星
更新时间：2021年1月26日
"""


import json
import requests
import socket
import re
import time

import settings
from Utils.timers import Timer


class ProxyUtils(object):
    def __init__(self, logger=None):
        self.logger = logger
        self.timer = Timer()

    # 获取代理
    def proxy_service_request(self, url, msg):
        self.timer.start()
        for _i in range(3):
            try:
                r = requests.get(url=url, timeout=10)
                resp = r.text
                # print(proxy)
                if resp:
                    self.logger.info('proxy | {} 成功 | use time: {}'.format(msg, self.timer.use_time()))
                    return resp
                else:
                    self.logger.error('proxy | {} 失败'.format(msg))
                    time.sleep(3)
                    continue

            except Exception as e:
                self.logger.error('proxy | {} 失败 | {}'.format(msg, e))
                time.sleep(3)
                continue
        else:
            self.logger.error('proxy | {} 失败 | use time: {}'.format(msg, self.timer.use_time()))
            return

    def add_proxy(self, ip, p='http', remain_time=30):
        return self.proxy_service_request(settings.ADD_PROXY_API.format(ip, p, remain_time), "增加代理 {}".format(ip))

    # 获取代理
    def get_proxy(self, ws="", protocol="http", using_time=30):
        return self.proxy_service_request(settings.GET_PROXY_API.format(ws, protocol, using_time), "获取代理")

    # 代理权重减1
    def release_proxy(self, ip, result):
        return self.proxy_service_request(settings.RELEASE_PROXY_API.format(ip, result), "释放代理 {}".format(ip))

    # 检测代理IP是否是高匿代理， 高匿返回True， 否则返回Fales
    def _jianChaNiMingDu(self, **proxies):
        local_ip = ''
        proxy_ip = ''
        # 获取本地外网IP
        local_resp = requests.get('https://httpbin.org/ip')
        if local_resp.status_code == 200:
            local_ip = json.loads(local_resp.content.decode('utf-8'))['origin']
            self.logger.info('proxy | 检测到本地IP: %s' % local_ip)

        # 获取使用代理返回IP
        proxy_resp = requests.get(url='https://httpbin.org/ip', proxies=proxies)
        if proxy_resp.status_code == 200:
            proxy_ip = json.loads(proxy_resp.content.decode('utf-8'))['origin']
            self.logger.info('proxy | 检测到代理IP: %s' % proxy_ip)

        # 判断代理是否高匿
        if local_ip not in proxy_ip:
            return True
        else:
            return False

    # 获取阿布云动态版代理
    def get_abuyun_proxy(self):
        proxy_host = "http-dyn.abuyun.com"
        proxy_port = "9020"

        # 代理隧道验证信息
        proxy_user = "H1A955UYUR3S8RXD"
        proxy_pass = "6FD2F11DD2337CF0"

        proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxy_host,
            "port": proxy_port,
            "user": proxy_user,
            "pass": proxy_pass,
        }

        proxies = {
            "http": proxy_meta,
            "https": proxy_meta,
        }
        return proxies

    # 获取本机内网IP
    @staticmethod
    def get_local_ip():
        global s
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            # self.logging.info('本地内网IP: %s' % ip)

            return ip
        except:
            s.close()
            return None


if __name__ == '__main__':
    proxier = ProxyUtils()
    print(proxier.get_proxy())
