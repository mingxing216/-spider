# -*-coding:utf-8-*-

'''

'''
import sys
import os
import urllib3
import re
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class TaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(TaskDownloader, self).__init__(logging=logging,
                                             timeout=timeout,
                                             proxy_type=proxy_type,
                                             proxy_country=proxy_country)

    # 网页正常度检测机制
    def __judge_verify(self, param):
        # 下载
        resp = self._startDownload(param=param)
        if resp['status'] == 0:
            response = resp['data']
            if '请输入验证码' in response.text or len(response.text) < 20:
                self.logging.info('出现验证码')
                # 重新下载
                return {'status': 2}

        return resp

    def getResp(self, url, mode, data=None, cookies=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua(),
        }
        # 设置post参数
        param['data'] = data
        # 设置cookies
        param['cookies'] = cookies

        return self.__judge_verify(param=param)

    # 创建COOKIE
    def create_cookie(self):
        url1 = 'http://kns.cnki.net/kns/request/NaviGroup.aspx?code=A&tpinavigroup=SOPDtpiresult&catalogName=SOPD_IPCCLS&__=Mon%20Feb%2018%202019%2016%3A52%3A06%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
        resp = self.getResp(url=url1, mode='GET')
        if resp['status'] == 0:
            try:
                return resp['data'].headers['Set-Cookie']
            except:
                return None

        return None

    # 获取时间列表
    def getTimeListResp(self, category, country, cookie):
        self._one(category=category, country=country, cookie=cookie)
        self._two(category=category, country=country, cookie=cookie)
        self._third(category=category, country=country, cookie=cookie)

        url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx?action=1&Param=ASP.brief_result_aspx%23SOPD/%u5E74/%u5E74%2Ccount%28*%29/%u5E74/%28%u5E74%2C%27date%27%29%23%u5E74%24desc/1000000%24/-/40/40000/ButtonView'
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
            proxies = self.downloader.proxy_obj.getProxy()
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

    def _one(self, category, country, cookie):
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
            'Referer': 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SOPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SOPD',
            'DbCatalog': '国外专利数据库',
            'ConfigFile': 'SOPD.xml',
            'db_opt': 'SCOD',
            'db_value': '国外专利数据库',
            'hdnUSPSubDB': '{}'.format(country),
            'his': '0'
        }

        return self._startDownload(param=param)

    def _two(self, category, country, cookie):
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
            'Referer': 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': 'webGroup',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SOPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SOPD',
            'DbCatalog': '国外专利数据库',
            'ConfigFile': 'SOPD.xml',
            'db_opt': 'SCOD',
            'db_value': '国外专利数据库',
            'hdnUSPSubDB': '{}'.format(country),
            'his': '0'
        }

        return self._startDownload(param=param)

    def _third(self, category, country, cookie):
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
            'Referer': 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'action': '44',
            'gt': '0',
            'NaviCode': '{}'.format(category),
            'catalogName': 'SOPD_IPCCLS',
            'ua': '1.25',
            'isinEn': '0',
            'PageName': 'ASP.brief_result_aspx',
            'DbPrefix': 'SOPD',
            'DbCatalog': '国外专利数据库',
            'ConfigFile': 'SOPD.xml',
            'db_opt': 'SCOD',
            'db_value': '国外专利数据库',
            'hdnUSPSubDB': '{}'.format(country),
            'his': '0'
        }

        return self._startDownload(param=param)

    def getIndexHtml(self, year, cookie):
        url = 'http://kns.cnki.net/kns/brief/brief.aspx?action=5&dbPrefix=SOPD&PageName=ASP.brief_result_aspx&Param=%E5%B9%B4%20=%20%27{}%27&recordsperpage=50'.format(
            year)
        # 设置请求头
        headers = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = headers

        return self.__judge_verify(param=param)

    def getNextHtml(self, url, cookie):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'Cookie': cookie,
            'User-Agent': user_agent_u.get_ua()
        }

        return self.__judge_verify(param=param)


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country):
        super(Downloader, self).__init__(logging=logging,
                                         timeout=timeout,
                                         proxy_type=proxy_type,
                                         proxy_country=proxy_country)

    # 网页正常度检测机制
    def __judge_verify(self, param):
        while True:
            # 下载
            resp = self._startDownload(param=param)
            if resp['status'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 20:
                    self.logging.info('出现验证码')
                    # 重新下载
                    continue

            return resp

    def getResp(self, url, mode, data=None, cookies=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data
        # 设置cookies
        param['cookies'] = cookies

        return self.__judge_verify(param=param)


