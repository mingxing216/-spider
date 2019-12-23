# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import time
import requests
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u
from Utils import proxy
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class GongKaiDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(GongKaiDownloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate, br',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                'Host': 'dbpub.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
                '''
                如果未设置请求异常的时间戳，则现在设置；
                如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                {'status': 1}
                '''
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    # 获取当前时间戳
                    now = int(time.time())
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        # url = 'http://kns.cnki.net/kns/request/NaviGroup.aspx?code=A&tpinavigroup=SCPD_FMtpiresult&catalogName=SCPD_IPCCLS&__=Wed%20Nov%2027%202019%2015%3A00%3A02%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
        url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SCPD_FM'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['code'] == 0:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None

    # 获取时间列表
    def getTimeListResp(self, referer, category, cookie):
        self._one(referer=referer, category=category, cookie=cookie)
        self._two(referer=referer, category=category, cookie=cookie)
        self._third(referer=referer, category=category, cookie=cookie)
        self._four(referer=referer, cookie=cookie)

        # url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SOPD/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
        url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SCPD_FM/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
        # 设置请求头
        headers = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }

        return self.__urllib2Download(url=url, headers=headers)

    def __urllib2Download(self, url, headers):

        # 请求异常时间戳
        err_time = 0
        while 1:
            proxies = self.proxy_obj.getProxy()
            proxies_http = re.findall(r"(\d+\.\d+\.\d+\.\d+:\d+)", proxies['http'])[0]
            proxy = urllib3.ProxyManager('http://{}'.format(proxies_http), headers=headers)
            try:
                begin_time = int(time.time())
                resp = proxy.request(method='get', url=url, timeout=10)
                end_time = int(time.time())
                self.logging.info(
                    'request for url: {} | mode: GET | data: None | proxy: {} | use time : {}s'.format(url,
                                                                                                       proxies,
                                                                                                       end_time - begin_time))
                return resp.data.decode('utf-8')
            except:
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    now = int(time.time())
                    # 判断从开始发生异常到现在是否超过了90秒
                    if now - err_time >= 90:
                        return None
                    else:
                        continue

    def _one(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/SearchHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_FM',
            'DbCatalog': '中国专利数据库_发明专利',
            'ConfigFile': 'SCPD_FM.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明专利',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _two(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/GetWebGroupHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': 'webGroup',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_FM',
            'DbCatalog': '中国专利数据库_发明专利',
            'ConfigFile': 'SCPD_FM.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明专利',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _third(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/group/doGroupLeft.aspx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '44',
            'gt': '0',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_FM',
            'DbCatalog': '中国专利数据库_发明专利',
            'ConfigFile': 'SCPD_FM.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明专利',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _four(self, referer, cookie):
        param = {'url': 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=0&dbPrefix=SCPD_FM&ConfigFile=SCPD_FM.xml'}
        param['mode'] = 'GET'
        param['headers'] = {
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }

        # 设置proxy
        param['proxies'] = self.proxy_obj.getProxy()

        return self._startDownload(param=param)


class ShouQuanDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(ShouQuanDownloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                'Host': 'dbpub.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
                '''
                如果未设置请求异常的时间戳，则现在设置；
                如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                {'status': 1}
                '''
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    # 获取当前时间戳
                    now = int(time.time())
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        # url = 'http://kns.cnki.net/kns/request/NaviGroup.aspx?code=A&tpinavigroup=SCPD_FMtpiresult&catalogName=SCPD_IPCCLS&__=Wed%20Nov%2027%202019%2015%3A00%3A02%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
        url = 'http://kns.cnki.net/kns/brief/result.aspx?dbPrefix=SCPD_SQ'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['code'] == 0:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None

    # 获取时间列表
    def getTimeListResp(self, referer, category, cookie):
        self._one(referer=referer, category=category, cookie=cookie)
        self._two(referer=referer, category=category, cookie=cookie)
        self._third(referer=referer, category=category, cookie=cookie)
        self._four(referer=referer, cookie=cookie)

        url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SCPD_SQ/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
        # 设置请求头
        headers = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }

        return self.__urllib2Download(url=url, headers=headers)

    def __urllib2Download(self, url, headers):

        # 请求异常时间戳
        err_time = 0
        while 1:
            proxies = self.proxy_obj.getProxy()
            proxies_http = re.findall(r"(\d+\.\d+\.\d+\.\d+:\d+)", proxies['http'])[0]
            proxy = urllib3.ProxyManager('http://{}'.format(proxies_http), headers=headers)
            try:
                begin_time = int(time.time())
                resp = proxy.request(method='get', url=url, timeout=10)
                end_time = int(time.time())
                self.logging.info(
                    'request for url: {} | mode: GET | data: None | proxy: {} | use time : {}s'.format(url,
                                                                                                       proxies,
                                                                                                       end_time - begin_time))
                return resp.data.decode('utf-8')
            except:
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    now = int(time.time())
                    # 判断从开始发生异常到现在是否超过了90秒
                    if now - err_time >= 90:
                        return None
                    else:
                        continue

    def _one(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/SearchHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_SQ',
            'DbCatalog': '中国专利数据库_发明授权',
            'ConfigFile': 'SCPD_SQ.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明授权',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _two(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/GetWebGroupHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': 'webGroup',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_SQ',
            'DbCatalog': '中国专利数据库_发明授权',
            'ConfigFile': 'SCPD_SQ.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明授权',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _third(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/group/doGroupLeft.aspx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '44',
            'gt': '0',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_SQ',
            'DbCatalog': '中国专利数据库_发明授权',
            'ConfigFile': 'SCPD_SQ.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_发明授权',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _four(self, referer, cookie):
        param = {'url': 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=0&dbPrefix=SCPD_SQ&ConfigFile=SCPD_SQ.xml'}
        param['mode'] = 'GET'
        param['headers'] = {
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }

        # 设置proxy
        param['proxies'] = self.proxy_obj.getProxy()

        return self._startDownload(param=param)


class WaiGuanDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(WaiGuanDownloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                'Host': 'dbpub.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
                '''
                如果未设置请求异常的时间戳，则现在设置；
                如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                {'status': 1}
                '''
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    # 获取当前时间戳
                    now = int(time.time())
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SCPD_WG'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['code'] == 0:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None

    # 获取时间列表
    def getTimeListResp(self, referer, category, cookie):
        self._one(referer=referer, category=category, cookie=cookie)
        self._two(referer=referer, category=category, cookie=cookie)
        self._third(referer=referer, category=category, cookie=cookie)
        self._four(referer=referer, cookie=cookie)

        url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SCPD_WG/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
        # 设置请求头
        headers = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }

        return self.__urllib2Download(url=url, headers=headers)

    def __urllib2Download(self, url, headers):

        # 请求异常时间戳
        err_time = 0
        while 1:
            proxies = self.proxy_obj.getProxy()
            proxies_http = re.findall(r"(\d+\.\d+\.\d+\.\d+:\d+)", proxies['http'])[0]
            proxy = urllib3.ProxyManager('http://{}'.format(proxies_http), headers=headers)
            try:
                begin_time = int(time.time())
                resp = proxy.request(method='get', url=url, timeout=10)
                end_time = int(time.time())
                self.logging.info(
                    'request for url: {} | mode: GET | data: None | proxy: {} | use time : {}s'.format(url,
                                                                                                       proxies,
                                                                                                       end_time - begin_time))
                return resp.data.decode('utf-8')
            except:
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    now = int(time.time())
                    # 判断从开始发生异常到现在是否超过了90秒
                    if now - err_time >= 90:
                        return None
                    else:
                        continue

    def _one(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/SearchHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_WGCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_WG',
            'DbCatalog': '中国专利数据库_外观设计',
            'ConfigFile': 'SCPD_WG.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_外观设计',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _two(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/request/GetWebGroupHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': 'webGroup',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_WGCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_WG',
            'DbCatalog': '中国专利数据库_外观设计',
            'ConfigFile': 'SCPD_WG.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_外观设计',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _third(self, referer, category, cookie):
        param = {'url': 'http://kns.cnki.net/kns/group/doGroupLeft.aspx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'http://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '44',
            'gt': '0',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_WGCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_WG',
            'DbCatalog': '中国专利数据库_外观设计',
            'ConfigFile': 'SCPD_WG.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_外观设计',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _four(self, referer, cookie):
        param = {'url': 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=0&dbPrefix=SCPD_WG&ConfigFile=SCPD_WG.xml'}
        param['mode'] = 'GET'
        param['headers'] = {
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }

        # 设置proxy
        param['proxies'] = self.proxy_obj.getProxy()

        return self._startDownload(param=param)


class ShiYongDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(ShiYongDownloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 每次请求的等待时间
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'Accept-Language': 'zh-CN,zh;q=0.9',
                # 'Accept-Encoding': 'gzip, deflate',
                # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Referer': referer,
                'Connection': 'close',
                'Host': 'dbpub.cnki.net',
                'User-Agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data'], 'proxies': param['proxies']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
                '''
                如果未设置请求异常的时间戳，则现在设置；
                如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                {'status': 1}
                '''
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    # 获取当前时间戳
                    now = int(time.time())
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        url = 'https://kns.cnki.net/kns/brief/result.aspx?dbprefix=SCPD_XX'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['code'] == 0:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies), resp['data'].headers['Set-Cookie']

        except:
            self.logging.error('cookie创建异常')
            return None

    # 获取时间列表
    def getTimeListResp(self, referer, category, cookie):
        self._one(referer=referer, category=category, cookie=cookie)
        self._two(referer=referer, category=category, cookie=cookie)
        self._third(referer=referer, category=category, cookie=cookie)
        # self._four(referer=referer, cookie=cookie)

        url = 'https://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SCPD_XX/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
        # 设置请求头
        headers = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }

        return self.__urllib2Download(url=url, headers=headers)

    def __urllib2Download(self, url, headers):

        # 请求异常时间戳
        err_time = 0
        while 1:
            proxies = self.proxy_obj.getProxy()
            proxies_http = re.findall(r"(\d+\.\d+\.\d+\.\d+:\d+)", proxies['https'])[0]
            proxy = urllib3.ProxyManager('https://{}'.format(proxies_http), headers=headers)
            try:
                begin_time = int(time.time())
                resp = proxy.request(method='get', url=url, timeout=10)
                end_time = int(time.time())
                self.logging.info(
                    'request for url: {} | mode: GET | data: None | proxy: {} | use time : {}s'.format(url,
                                                                                                       proxies,
                                                                                                       end_time - begin_time))
                return resp.data.decode('utf-8')
            except:
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    now = int(time.time())
                    # 判断从开始发生异常到现在是否超过了90秒
                    if now - err_time >= 90:
                        return None
                    else:
                        continue

    def _one(self, referer, category, cookie):
        param = {'url': 'https://kns.cnki.net/kns/request/SearchHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'https://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_XX',
            'DbCatalog': '中国专利数据库_实用新型',
            'ConfigFile': 'SCPD_XX.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_实用新型',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _two(self, referer, category, cookie):
        param = {'url': 'https://kns.cnki.net/kns/request/GetWebGroupHandler.ashx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'https://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': 'webGroup',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_XX',
            'DbCatalog': '中国专利数据库_实用新型',
            'ConfigFile': 'SCPD_XX.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_实用新型',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _third(self, referer, category, cookie):
        param = {'url': 'https://kns.cnki.net/kns/group/doGroupLeft.aspx'}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Origin': 'https://kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '44',
            'gt': '0',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SCPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SCPD_XX',
            'DbCatalog': '中国专利数据库_实用新型',
            'ConfigFile': 'SCPD_XX.xml',
            'db_opt': 'SCOD',
            'db_value': '中国专利数据库_实用新型',
            'his': '0'
        }

        return self._startDownload(param=param)

    def _four(self, referer, cookie):
        param = {'url': 'https://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=0&dbPrefix=SCPD_XX&ConfigFile=SCPD_XX.xml'}
        param['mode'] = 'GET'
        param['headers'] = {
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Cookie': cookie,
            'Host': 'kns.cnki.net',
            'Referer': referer,
            'User-Agent': user_agent_u.get_ua()
        }

        # 设置proxy
        param['proxies'] = self.proxy_obj.getProxy()

        return self._startDownload(param=param)


