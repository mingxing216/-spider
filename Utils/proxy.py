# -*-coding:utf-8-*-
'''
简介：本文件是框架内部功能文件，除框架开发人员，任何人不可对本文件代码进行任何形式的更改。
     主要负责提供代理池代理增、删、改、查操作接口
开发人：采集部-王勇
更新人：
开发时间：2019年01月04日
更新时间：
'''


import os
import sys
import json
import requests
import socket
import re
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings


# 代理IP操作类
class ProxyUtils(object):
    def __init__(self, logging, type=None, random=0, country=1, city=0):
        '''
        :param logging: log对象，实例化参数
        :param type: 所需代理IP种类，实例化参数
        :param random: 是否随机获取
        :param country: 国家 1：中国大陆
        '''
        assert type == 'http' or type == 'https' or type == 'socks5' or type == 'adsl' or type == None

        self.logging = logging
        self.type = type
        self.random = random
        self.country = country
        self.city = city


    def __del(self, ip):
        url = '{}?ip={}'.format(settings.DELETE_PROXY_API, ip)
        try:
            resp = requests.get(url=url).content.decode('utf-8')
            data = json.loads(resp)
            if data['status'] == 0:
                self.logging.info('delete proxy {} OK'.format(ip))
        except:
            pass

    def __update(self, ip):
        url = '{}?ip={}'.format(settings.UPDATE_PROXY_API, ip)
        try:
            resp = requests.get(url=url).content.decode('utf-8')
            data = json.loads(resp)
            if data['status'] == 0:
                self.logging.info('delete proxy {} OK'.format(ip))
        except:
            pass

    # 检测代理IP是否是高匿代理， 高匿返回True， 否则返回Fales
    def __jianChaNiMingDu(self, **proxies):
        local_ip = ''
        proxy_ip = ''
        # 获取本地外网IP
        local_resp = requests.get('https://httpbin.org/ip')
        if local_resp.status_code == 200:
            local_ip = json.loads(local_resp.content.decode('utf-8'))['origin']
            self.logging.info('检测到本地IP: %s' % local_ip)

        # 获取使用代理返回IP
        proxy_resp = requests.get(url='https://httpbin.org/ip', proxies=proxies)
        if proxy_resp.status_code == 200:
            proxy_ip = json.loads(proxy_resp.content.decode('utf-8'))['origin']
            self.logging.info('检测到代理IP: %s' % proxy_ip)

        # 判断代理是否高匿
        if local_ip not in proxy_ip:
            return True
        else:
            return False

    # 获取代理
    def get_proxy(self):
        while True:
            try:
                r = requests.get(settings.GET_PROXY_API)
                ip = r.text
                # print(proxy)
                if ip:
                    return ip
                else:
                    self.logging.error('代理池代理获取失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('代理池代理获取失败')
                time.sleep(3)
                continue

    # 设置代理最大权重
    def max_proxy(self, ip):
        while True:
            try:
                r = requests.get(settings.MAX_PROXY_API.format(ip))
                num = r.text
                # print(proxy)
                if num:
                    return num
                else:
                    self.logging.error('代理最大权重设置失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('代理最大权重设置失败')
                time.sleep(3)
                continue

    # 代理权重减1
    def dec_proxy(self, ip):
        while True:
            try:
                r = requests.get(settings.DEC_PROXY_API.format(ip))
                num = r.text
                # print(proxy)
                if num:
                    return num
                else:
                    self.logging.error('代理权重 -1 失败')
                    time.sleep(3)
                    continue

            except Exception:
                self.logging.error('代理权重 -1 失败')
                time.sleep(3)
                continue

    # 获取代理
    def getProxy(self):
        while True:
            try:
                r = requests.get('http://60.195.249.95:5000/random')
                proxy = r.text
                # print(proxy)
                if proxy:
                    return {'http': 'http://' + proxy,
                            'https': 'https://' + proxy}
                else:
                    self.logging.error('代理池代理获取失败')
                    time.sleep(2)
                    continue

            except Exception:
                self.logging.error('代理接口请求失败')
                time.sleep(2)
                continue

    # # 获取代理
    # def getProxy(self):
    #     while True:
    #         url = "{}?random={}&country={}&city={}&type={}".format(settings.GET_PROXY_API, self.random,
    #                                                                self.country, self.city, self.type)
    #
    #         try:
    #             proxy_data = requests.get(url=url).content.decode('utf-8')
    #         except:
    #             proxy_data = None
    #
    #         if proxy_data:
    #             data = json.loads(proxy_data)
    #             if data['status'] == 0:
    #                 ip = data['ip']
    #                 port = data['port']
    #                 proxy_ip = 'https://' + ip + ':' + port
    #
    #                 # # 判断是否为高匿代理
    #                 # allow = self.__jianChaNiMingDu(https=proxy_ip)
    #                 # print(allow)
    #                 # if allow:
    #
    #                 # 判断协议种类
    #                 if self.type == 'http':
    #                     return {'http': 'http://{}:{}'.format(ip, port)}
    #
    #                 elif self.type == 'https':
    #                     return {'https': 'https://{}:{}'.format(ip, port)}
    #
    #                 elif self.type == 'socks5':
    #                     return {'http': 'socks5://{}:{}'.format(ip, port),
    #                             'https': 'socks5://{}:{}'.format(ip, port)}
    #
    #                 elif self.type == 'adsl':
    #                     # return {'http': 'http://{}:{}'.format(ip, port)}
    #
    #                     return {'http': 'http://{}:{}'.format(ip, port),
    #                             'https': 'https://{}:{}'.format(ip, port)}
    #
    #                 else:
    #                     self.logging.error('status: False | err: type error!!! | from: getProxy')
    #
    #                     continue
    #
    #                 # else:
    #                 #     self.logging.error('代理非高匿代理，获取失败')
    #                 #     continue
    #
    #             else:
    #                 self.logging.error('代理池代理获取失败')
    #                 time.sleep(5)
    #
    #             continue
    #
    #         else:
    #             self.logging.error('代理池代理获取失败')
    #             time.sleep(5)
    #             continue

    # 删除代理
    def delProxy(self, proxies):
        # 判断协议种类
        if self.type == 'http':
            ip = re.findall(r"http://(.*):", proxies['http'])[0]
            self.__del(ip)

        elif self.type == 'https':
            ip = re.findall(r"https://(.*):", proxies['https'])[0]
            self.__del(ip)

        elif self.type == 'socks5':
            ip = re.findall(r"socks5://(.*):", proxies['http'])[0]
            self.__del(ip)

        elif self.type == 'adsl':
            ip = re.findall(r"http://(.*):", proxies['http'])[0]
            self.__update(ip)

        else:
            self.logging.error('status: False | err: type error!!! | from: delProxy')

    # 获取阿布云动态版代理
    def getABuYunProxy(self):
        proxyHost = "http-dyn.abuyun.com"
        proxyPort = "9020"

        # 代理隧道验证信息
        proxyUser = "H1A955UYUR3S8RXD"
        proxyPass = "6FD2F11DD2337CF0"

        proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxyHost,
            "port": proxyPort,
            "user": proxyUser,
            "pass": proxyPass,
        }

        proxies = {
            "http": proxyMeta,
            "https": proxyMeta,
        }
        return proxies

    # 获取本机内网IP
    def getLocalIP(self):
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
