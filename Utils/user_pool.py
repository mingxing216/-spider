# -*- coding:utf-8 -*-

"""
简介：本文件是框架内部功能文件，除框架开发人员，任何人不可对本文件代码进行任何形式的更改。
     主要负责提供用户池代理增、删、改、查操作接口
开发人：采集部-张明星
更新人：
开发时间：2020年09月16日
更新时间：
"""

import os
import sys
import json
import requests
import socket
import time

import settings


# cookie池操作类
class CookieUtils(object):
    def __init__(self, logging=None):
        """
        :param logging: log对象，实例化参数
        """
        self.logging = logging

    # 随机获取一个cookie
    def get_cookie(self):
        stat = time.time()
        for _i in range(3):
            try:
                r = requests.get(settings.GET_COOKIE_API)
                cookie_info = json.loads(r.text)
                cookie = cookie_info['cookie']
                # print(cookie)
                if cookie:
                    self.logging.info('handle | 获取cookie成功 | use time: {}'.format('%.3f' % (time.time() - stat)))
                    return cookie_info
                else:
                    self.logging.error('用户池cookie获取失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('用户池cookie获取失败')
                time.sleep(3)
                continue
        else:
            self.logging.info('handle | 获取cookie失败 | use time: {}'.format('%.3f' % (time.time() - stat)))
            return

    # cookie使用次数加 1
    def inc_cookie(self, username):
        stat = time.time()
        for _i in range(3):
            try:
                r = requests.get(settings.INC_COOKIE_API.format(username))
                num = r.text
                # print(proxy)
                if num:
                    self.logging.info('handle | Cookie次数 +1 成功 | use time: {}'.format('%.3f' % (time.time() - stat)))
                    return num
                else:
                    self.logging.error('Cookie 次数 +1 失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('Cookie 次数 +1 失败')
                time.sleep(3)
                continue
        else:
            self.logging.info('handle | Cookie次数 +1 失败 | use time: {}'.format('%.3f' % (time.time() - stat)))
            return

    # cookie使用次数加 50
    def max_cookie(self, username):
        stat = time.time()
        for _i in range(3):
            try:
                r = requests.get(settings.MAX_COOKIE_API.format(username))
                num = r.text
                # print(proxy)
                if num:
                    self.logging.info('handle | Cookie次数 +50 成功 | use time: {}'.format('%.3f' % (time.time() - stat)))
                    return num
                else:
                    self.logging.error('Cookie 次数 +50 失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('Cookie 次数 +50 失败')
                time.sleep(3)
                continue
        else:
            self.logging.info('handle | Cookie次数 +50 失败 | use time: {}'.format('%.3f' % (time.time() - stat)))
            return

    # cookie使用次数减 1
    def dec_cookie(self, username):
        stat = time.time()
        for _i in range(3):
            try:
                r = requests.get(settings.DEC_COOKIE_API.format(username))
                num = r.text
                # print(proxy)
                if num:
                    self.logging.info('handle | Cookie次数 -1 成功 | use time: {}'.format('%.3f' % (time.time() - stat)))
                    return num
                else:
                    self.logging.error('Cookie次数 -1 失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('Cookie次数 -1 失败')
                time.sleep(3)
                continue
        else:
            self.logging.info('handle | Cookie次数 -1 失败 | use time: {}'.format('%.3f' % (time.time() - stat)))
            return

    # 获取本机内网IP
    @property
    def get_local_ip(self):
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
