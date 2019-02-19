# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import ast
import urllib3
from lxml import html
etree = html.etree


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


# # COOKIE = 'UM_distinctid=1673f770eeb133e-0d8bbb42a85326-35667607-13c680-1673f770eed42; Ecp_ClientId=4181123152702026117; cnkiUserKey=f7c89626-bf4a-c453-a1b5-dd0b532d4dc8; CNZZDATA3258975=cnzz_eid%3D408869683-1542962027-http%253A%252F%252Fnavi.cnki.net%252F%26ntime%3D1544423970; RsPerPage=50; ASP.NET_SessionId=kjgepovlwokc5ry1kw0eobuf; SID_kns=123111; SID_kinfo=125105; SID_klogin=125143; KNS_SortType=; SID_krsnew=125131; LID=WEEvREcwSlJHSldRa1Fhb09jSnZpSUx6ZU51Y1dmTVhnYlNUYXhPdEp4bz0=$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4ggI8Fm4gTkoUKaID8j8gFw!!; SID_kcms=124108; Ecp_IpLoginFail=190118103.36.220.170'
# COOKIE = ''

class UrlDownloader(downloader.BaseDownloaderMiddleware):
    # 创建COOKIE
    def create_cookie(self):
        url1 = 'http://kns.cnki.net/kns/request/NaviGroup.aspx?code=A&tpinavigroup=SOPDtpiresult&catalogName=SOPD_IPCCLS&__=Mon%20Feb%2018%202019%2016%3A52%3A06%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
        resp = self.getResp(url=url1)
        return resp.headers['Set-Cookie']

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                resp = resp['data']
                if len(resp.content.decode('utf-8')) < 20:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                if '请输入验证码' in resp.content.decode('utf-8'):
                    self.logging.error('出现验证码')
                    # 删除代理
                    # self.__del_proxies(proxies=proxies)

                    return None

                return resp

            return resp['data']

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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], param['url'], param['data']))
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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], param['url'], param['data']))
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

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], param['url'], param['data']))
        return self._startDownload(param=param)
    
    def __urllib2Download(self, url, headers):

        for i in range(5):
            proxies = self.downloader.proxy_obj.getProxy()
            proxies_http = re.findall(r"(\d+\.\d+\.\d+\.\d+:\d+)", proxies['http'])[0]
            proxy = urllib3.ProxyManager('http://{}'.format(proxies_http), headers=headers)
            try:
                resp = proxy.request(method='get', url=url, timeout=5)
                return resp.data.decode('utf-8')
            except:
                # 删除代理
                self.downloader.proxy_obj.delProxy(proxies)
                continue

        return None

    def getResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)

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

    def getIndexHtml(self, year, cookie):
        url = 'http://kns.cnki.net/kns/brief/brief.aspx?action=5&dbPrefix=SOPD&PageName=ASP.brief_result_aspx&Param=%E5%B9%B4%20=%20%27{}%27&recordsperpage=50'.format(year)
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


class DataDownloader(downloader.BaseDownloaderMiddleware):

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                resp = resp['data']
                if len(resp.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp['data']

    def getIndexResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, data))
        return self.__judge_verify(param=param)


class Downloader(downloader.BaseDownloaderMiddleware):

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                resp = resp['data']
                if len(resp.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp['data']

    def getResp(self, url, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = 'get'
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, data))
        return self.__judge_verify(param=param)























