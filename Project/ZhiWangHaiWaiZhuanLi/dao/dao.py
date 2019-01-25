# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import base64
import hashlib
import requests
import re

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import proxy
from Utils import mysqlpool_utils
from Utils import redis_pool
from Project.ZhiWangHaiWaiZhuanLi import config


class UrlDao(object):
    def __init__(self, logging):
        self.logging = logging
        self.mysql_client = mysqlpool_utils.MysqlPool()
        self.table = config.MYSQL_URL_TABLE

    # 保存任务url到mysql数据库
    def saveUrlToMysql(self, url):
        data = {
            'url': url
        }
        try:
            self.mysql_client.insert_one(table=self.table, data=data)
        except:
            pass
        # self.logging.info('保存种子: {}'.format(url))


class DataDao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        self.table = config.MYSQL_URL_TABLE
        self.mysql_client = mysqlpool_utils.MysqlPool()
        self.redis_client = redis_pool.RedisPoolUtils()

    # 从redis获取100个任务
    def getUrlList(self):
        url_data = self.redis_client.queue_spops(key=config.REDIS_URL_TABLE,
                                                 count=config.REDIS_GET_NUMBER,
                                                 lockname='get_zhiwang_zhuanli_lock')

        return url_data

    # 从mysql删除任务
    def deleteObject(self, url):
        sql = "delete from {} where url = '{}'".format(self.table, url)
        self.mysql_client.execute(sql=sql)


    # 存储专利数据到Hbase数据库
    def saveDataToHbase(self, data):
        save_data = json.dumps(data)
        url = '{}'.format(settings.SpiderDataSaveUrl)
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "python",
                "ref": "",
                "item": save_data}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        resp = requests.post(url=url, headers=headers, data=data)

        return resp


    # 保存流媒体到hbase
    def saveMediaToHbase(self, media_url, content, type):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        content_bs64 = base64.b64encode(content)
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
        item = {
            'pk': sha,
            'type': type,
            'url': media_url
        }
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "100",
                "url": "{}".format(media_url),
                "content": "{}".format(content_bs64.decode('utf-8')),
                "type": "{}".format(type),
                "ref": "",
                "item": json.dumps(item)}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        resp = requests.post(url=url, headers=headers, data=data)

        return resp

    # # 保存媒体文件链接到mysql
    # def saveMediaToMysql(self, url, type):
    #     if re.match('http', url):
    #         assert type == 'image' or type == 'music' or type == 'video' or type == 'file'
    #         sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
    #         data = {
    #             'sha': sha,
    #             'type': type,
    #             'url': url
    #         }
    #         self.mysql_client.insert_one(table=settings.MEDIA_TABLE, data=data)


class Dao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        # self.mysql_client = mysqlpool_utils.MysqlPool()


    # 存储专利数据到Hbase数据库
    def saveDataToHbase(self, data):
        save_data = json.dumps(data)
        url = '{}'.format(settings.SpiderDataSaveUrl)
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "python",
                "ref": "",
                "item": save_data}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        resp = requests.post(url=url, headers=headers, data=data)

        return resp


    # 保存流媒体到hbase
    def saveMediaToHbase(self, media_url, content, type):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        content_bs64 = base64.b64encode(content)
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
        item = {
            'pk': sha,
            'type': type,
            'url': media_url
        }
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "100",
                "url": "{}".format(media_url),
                "content": "{}".format(content_bs64.decode('utf-8')),
                "type": "{}".format(type),
                "ref": "",
                "item": json.dumps(item)}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        resp = requests.post(url=url, headers=headers, data=data)

        return resp

    # # 保存媒体文件链接到mysql
    # def saveMediaToMysql(self, url, type):
    #     if re.match('http', url):
    #         assert type == 'image' or type == 'music' or type == 'video' or type == 'file'
    #         sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
    #         data = {
    #             'sha': sha,
    #             'type': type,
    #             'url': url
    #         }
    #         self.mysql_client.insert_one(table=settings.MEDIA_TABLE, data=data)