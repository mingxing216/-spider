# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
import re
import time
import json
import requests
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader_bofore
from Utils import user_agent_u
from Utils import proxy_pool
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy_pool.ProxyUtils(logger=logging, mode=proxy_type)

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
                # 'Content-Type': 'application/json',
                'Referer': referer,
                'Connection': 'close',
                # 'Host': 'navi.cnki.net',
                # 'Origin': 'https://navi.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置proxy
            proxies = None
            if self.proxy_type:
                ip = self.proxy_obj.get_proxy()
                proxies = {'http': 'http://' + ip,
                           'https': 'https://' + ip}

            # # 设置请求开始时间
            # start_time = time.time()

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)

            if down_data['code'] == 0:
                # 设置代理最大权重
                max = self.proxy_obj.max_proxy(ip)
                # print(max)
                # self.logging.info('请求成功: {} | 用时: {}秒'.format(url, '%.2f' %(time.time() - start_time)))
                return down_data['data']

            if down_data['code'] == 1:
                # 代理权重减1
                dec = self.proxy_obj.dec_proxy(ip)
                # print(dec)
                # self.logging.warning('请求内容错误: {} | 响应码: {} | 用时: {}秒'.format(url, down_data['status'], '%.2f' %(time.time() - start_time)))
                if stat_count > 5:
                    return
                else:
                    stat_count += 1
                    continue

            if down_data['code'] == 2:
                # 代理权重减1
                dec = self.proxy_obj.dec_proxy(ip)
                # print(dec)
                # self.logging.error('请求失败: {} | 错误信息: {} | 用时: {}秒'.format(url, down_data['message'], '%.2f' %(time.time() - start_time)))
                if err_count > 5:
                    return
                else:
                    err_count += 1
                    continue

    # 创建COOKIE
    def create_cookie(self, url):
        # url = 'https://navi.cnki.net/KNavi/PPaper.html?productcode=CDFD'
        try:
            resp = self.getResp(url=url, method='GET')
            if resp:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return resp.cookies
                # return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None

    # 创建COOKIE
    def getFenLei(self, s, value):
        self.getFirst(s)
        self.getSecond(s, value)

    def getFirst(self, s):
        url = 'https://navi.cnki.net/knavi/Common/LeftNavi/PPaper'
        data = {
            'productcode': 'CDMD',
            'index': 1,
            'random': random.random()
        }

        self.getResp(s=s, url=url, method='POST', data=data)

    def getSecond(self, s, value):
        url = 'https://navi.cnki.net/knavi/Common/Search/PPaper'
        data = {}
        data['SearchStateJson'] = json.dumps(
            {"StateID": "",
             "Platfrom": "",
             "QueryTime": "",
             "Account": "knavi",
             "ClientToken": "",
             "Language": "",
             "CNode": {"PCode": "CDMD",
                       "SMode": "",
                       "OperateT": ""},
             "QNode": {"SelectT": "",
                       "Select_Fields": "",
                       "S_DBCodes": "",
                       "QGroup": [
                           {"Key": "Navi",
                            "Logic": 1,
                            "Items": [],
                            "ChildItems": [
                                {"Key": "PPaper",
                                 "Logic": 1,
                                 "Items": [{"Key": 1,
                                            "Title": "",
                                            "Logic": 1,
                                            "Name": "AREANAME",
                                            "Operate": "",
                                            "Value": "{}?".format(value),
                                            "ExtendType": 0,
                                            "ExtendValue": "",
                                            "Value2": ""}],
                                 "ChildItems": []}
                            ]}
                       ],
                       "OrderBy": "RT|",
                       "GroupBy": "",
                       "Additon": ""}
             })
        data['displaymode'] = 1
        data['pageindex'] = 1
        data['pagecount'] = 21
        data['index'] = 1
        data['random'] = random.random()

        self.getResp(s=s, url=url, method='POST', data=data)

class QiKanLunWen_QiKanTaskDownloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(QiKanLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                              timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy_pool.ProxyUtils(logger=logging, mode=proxy_type, country=proxy_country, city=proxy_city)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)

    def getIndexHtml(self, url, data=None):
        param = {'url': url}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'productcode': 'CJFD',
            'index': 1
        }

        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenTaskDownloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenDataDownloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)


class ZhiWangLunWen_QiKanDataDownloader(downloader_bofore.BaseDownloader):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(ZhiWangLunWen_QiKanDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200 and len(response.text) > 0:
                    self.logging.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        return self.__judge_verify(param=param)