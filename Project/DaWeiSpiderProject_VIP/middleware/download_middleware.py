# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random
import json
import requests

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agents
from Utils import proxy_utils

class Download_Middleware():
    def __init__(self, logging):
        self.logging = logging
        self.post_url = 'http://www.innojoy.com/client/interface.aspx'


    def getOrangeApiData(self, url):
        '''获取橙子API返回参数'''
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForGet(url=url)

        return resp

    # 下载图片
    def downImg(self, url, ua, referer):
        headers = {
            'User-Agent': ua,
            'Referer': referer
        }
        resp = requests.get(url=url, headers=headers).content

        return resp

    # 获取大为账号参数响应
    def getUserGuid_resp(self, user, proxy, ua):
        url = 'http://www.innojoy.com/client/interface.aspx'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '348',
            'Content-Type': 'application/json',
            'Host': 'www.innojoy.com',
            'Origin': 'http://www.innojoy.com',
            'Referer': 'http://www.innojoy.com/account/login.html?p=V20181102',
            'User-Agent': ua,
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = json.dumps({
            'requestModule': 'UserManager',
            'userConfig': {
                'Action': 'Login',
                'EMail': user,
                'AreaCode': '86',
                'Password': user,
                'GUID': '',
                'ChkCode': '',
                'userAgent': ua,
                'remember': False
            },
            'systemConfig': {
                'SystemTitle': None
            },
            'language': 'zh'
        })
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForPost(url=url, data=data, proxies=proxy)

        return resp

    # 获取专利分类接口响应
    def getPatentType_resp(self, guid, proxy, ua):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '220',
            'Content-Type': 'application/json',
            'Host': 'www.innojoy.com',
            'Origin': 'http://www.innojoy.com',
            'Referer': 'http://www.innojoy.com/search/ipcsearch.htm',
            'User-Agent': ua,
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = json.dumps(
            {
                'requestModule': 'PatentSearch',
                'userId': guid,
                'patentSearchConfig': {
                    'Action': 'SearchIPC',
                    'GUID': None,
                    'Page': 0,
                    'PageSize': 0,
                    'pid': '',
                    'collection': '',
                    'IDCflag': 'ipcclass'
                },
                'language': 'zh'
            }
        )
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForPost(url=self.post_url, data=data, proxies=proxy)

        return resp

    # 获取专利地区分类接口响应
    def getRegion_resp(self, proxy, ua):
        url = ('http://www.innojoy.com/client/merge?'
               'p=V20181102'
               '&files=popdrop.js+clientstorage.js+comm.js+'
               'dawei.const.js+dawei_control.js+loadingproc.js:formatted')
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ua,
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForGet(url=url, proxies=proxy)

        return resp

    # 获取当前专利页响应
    def getPageResp(self, sic, region, page, proxy, ua, guid, page_guid):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '1031',
            'Content-Type': 'application/json',
            'Host': 'www.innojoy.com',
            'Origin': 'http://www.innojoy.com',
            'Referer': 'http://www.innojoy.com/searchresult/default.html',
            'User-Agent': ua,
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = json.dumps(
            {
                'requestModule': 'PatentSearch',
                'userId': guid,
                'patentSearchConfig': {
                    'Query': 'SIC=' + sic,
                    'TreeQuery': '',
                    'Database': region,
                    'Action': 'Search',
                    'DBOnly': 0,
                    'Page': '{}'.format(page),
                    'PageSize': '50',
                    'GUID': page_guid,
                    'Sortby': '',
                    'AddOnes': '',
                    'DelOnes': '',
                    'RemoveOnes': '',
                    'SmartSearch': '',
                    'TrsField': ''
                },
                'language': 'zh'
            }
        )
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForPost(url=self.post_url, data=data, proxies=proxy)

        return resp

    # 获取专利详情接口响应
    def getPatentApiResp(self, patent_url, userID, database, query, ua, proxy):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '238',
            'Content-Type': 'application/json',
            'Host': 'www.innojoy.com',
            'Origin': 'http://www.innojoy.com',
            'Referer': patent_url,
            'User-Agent': ua,
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = json.dumps(
            {
                'requestModule': 'PatentSearch',
                'userId': userID,
                'patentSearchConfig': {
                    'Database': database,
                    'PageSize': 1,
                    'Action': 'Search',
                    'ContainsFullText': True,
                    'LiceneCode': '',
                    'Query': 'DN={}'.format(query)
                },
                'language': 'zh'
            }
        )
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForPost(url=self.post_url, data=data, proxies=proxy)

        return resp


