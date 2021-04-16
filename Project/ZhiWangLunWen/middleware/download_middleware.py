# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time
import json
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u, timers
from ProxyPool.ProxyClient import proxy_client
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader.BaseDownloader):
    def __init__(self, logging, stream, timeout, proxy_enabled, cookie_obj=None):
        super(Downloader, self).__init__(logging=logging, stream=stream, timeout=timeout)
        self.proxy_enabled = proxy_enabled
        self.proxy_obj = proxy_client.ProxyPoolClient(logger=logging)
        self.cookie_obj = cookie_obj
        self.downloader_timer = timers.Timer()

    def get_resp(self, url, method, s=None, data=None, host=None, cookies=None, referer=None, ranges=None, user=None):
        self.logger.info('downloader start')
        self.downloader_timer.start()
        ret = self._get_resp(url, method, s=s, data=data, host=host, cookies=cookies, referer=referer,
                             ranges=ranges, user=user)
        if not ret:
            self.logger.info('downloader end | 下载失败 | use time: {}'.format(self.downloader_timer.use_time()))
            return

        if ret['code'] == 2:
            msg = 'downloader end | 下载失败, 页面响应失败, msg: {} | use time: {}'.format(ret['message'], self.downloader_timer.use_time())
            self.logger.error(msg)
            return

        if ret['code'] == 1:
            msg = 'downloader end | 下载失败, 页面响应状态码错误, status: {} | use time: {}'.format(ret['status'],
                                                                                       self.downloader_timer.use_time())
            self.logger.error(msg)
            return ret

        self.logger.info('downloader end | 下载成功 | use time: {}'.format(self.downloader_timer.use_time()))
        return ret

    def _get_resp(self, url, method, s=None, data=None, host=None, cookies=None, referer=None, ranges=None, user=None):
        # 响应状态码错误重试次数
        stat_count = 0
        # 请求异常重试次数
        err_count = 0
        while 1:
            # 设置请求头
            headers = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                # 'Content-Type': 'application/json',
                'Referer': referer,
                'Range': ranges,
                # 'Cookie': 'ASP.NET_SessionId=32nrqfxmdq0r5xcs05eac55d; skybug=46c629a8306c41bd731afe1b03760367; usercssn=UserID=376906&allcheck=732715F2D8B151F6113B09AD01A0352A',
                # 'Connection': 'close',
                'Host': host,
                # 'Origin': 'https://navi.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }

            # cookie使用次数+1
            if self.cookie_obj is not None and user is not None:
                self.cookie_obj.inc_cookie(user)

            # 设置proxy
            proxies = None
            ip = None
            if self.proxy_enabled:
                # 获取代理
                ip = self.proxy_obj.get_proxy()
                if ip:
                    proxies = {'http': 'http://' + ip,
                               'https': 'https://' + ip}

            # 获取响应
            down_data = self.begin(session=s, url=url, method=method, data=data, headers=headers, proxies=proxies,
                                   cookies=cookies)

            # 释放代理
            self.proxy_obj.release_proxy(ip, down_data['code'] == 0 or down_data['code'] == 1)

            # 判断
            if down_data is None:

                return

            # 返回值中添加IP信息
            down_data['proxy_ip'] = ip

            if down_data['code'] == 0:
                return down_data

            if down_data['code'] == 1:
                if down_data['status'] == 404:

                    return down_data
                else:
                    if stat_count > 3:

                        return down_data
                    else:
                        stat_count += 1
                        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                        continue

            if down_data['code'] == 2:
                if err_count > 3:

                    return down_data
                else:
                    err_count += 1
                    time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
                    continue

    # 创建COOKIE
    def create_cookie(self, url):
        # url = 'https://navi.cnki.net/KNavi/PPaper.html?productcode=CDFD'
        try:
            resp = self.get_resp(url=url, method='GET')
            if resp:
                # print(resp.cookies)
                self.logger.info('cookie创建成功')
                return resp.cookies
                # return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logger.error('cookie创建异常')
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

        self.get_resp(s=s, url=url, method='POST', data=data)

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

        self.get_resp(s=s, url=url, method='POST', data=data)


class QiKanLunWen_QiKanTaskDownloader(downloader.BaseDownloader):
    def __init__(self, logging, timeout, proxy_enabled, stream):
        super(QiKanLunWen_QiKanTaskDownloader, self).__init__(logging=logging, stream=stream, timeout=timeout)
        self.proxy_type = proxy_enabled
        self.proxy_obj = proxy_client.ProxyUtils(logger=logging)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200:
                    self.logger.info('出现验证码')
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


class QiKanLunWen_LunWenTaskDownloader(downloader.BaseDownloader):
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
                    self.logger.info('出现验证码')
                    # 更换代理重新下载
                    continue

            return resp

    def get_resp(self, url, mode, data=None):
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


class QiKanLunWen_LunWenDataDownloader(downloader.BaseDownloader):
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
                    self.logger.info('出现验证码')
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


class ZhiWangLunWen_QiKanDataDownloader(downloader.BaseDownloader):
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
                    self.logger.info('出现验证码')
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
