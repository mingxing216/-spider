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
from Utils import redis_pool
from Utils import mysqlpool_utils
from Project.ZhiWangPapers import config


class QiKanDao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        self.redis_client = redis_pool.RedisPoolUtils()
        self.mysql_client = mysqlpool_utils.MysqlPool()
        # 第一个期刊集合名
        self.first_name = 'qikan_queue_1'
        # 最后一个期刊集合名
        self.last_name = 'qikan_queue_2'
        

    def getData1(self):
        return self.redis_client.smembers(key=self.first_name)

    def getData2(self):
        return self.redis_client.smembers(key=self.last_name)

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

    # 保存媒体文件链接到mysql
    def saveMediaToMysql(self, url, type):
        if re.match('http', url):
            assert type == 'image' or type == 'music' or type == 'video' or type == 'file'
            sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
            data = {
                'sha': sha,
                'type': type,
                'url': url
            }
            self.mysql_client.insert_one(table=settings.MEDIA_TABLE, data=data)


class LunWenDao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        self.mysql_client = mysqlpool_utils.MysqlPool(config.MYSQLPOOL_NUMBER)
        self.redis_client = redis_pool.RedisPoolUtils(config.REDIS_POOL_NUMBER)

    # 存储论文url到mysql
    def saveProjectUrlToMysql(self, table, url_data):
        sha = hashlib.sha1(url_data['url'].encode('utf-8')).hexdigest()
        data = {
            'sha': sha,
            'memo': json.dumps(url_data)
        }
        try:
            self.mysql_client.insert_one(table=table, data=data)
            self.logging.info('insert: {}'.format(sha))

        except Exception as e:
            self.logging.warning(e)

    # 从论文队列获取100个论文任务
    def getLunWenUrls(self, table):
        sql = "select * from {} limit 100".format(table)
        datas = self.mysql_client.get_results(sql=sql)

        return datas

    # 从redis获取期刊任务
    def getQiKanUrlData(self, key, lockname):
        data = self.redis_client.queue_spop(key=key, lockname=lockname)

        return data

    # 判断论文是否抓取过
    def getLunWenStatus(self, table, sha):
        sql = "select * from {} where `sha` = '{}'".format(table, sha)
        status = self.mysql_client.get_results(sql=sql)
        if status:

            return True
        else:

            return False

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


    # 保存媒体文件链接到mysql
    def saveMediaToMysql(self, url, type):
        if re.match('http', url):
            assert type == 'image' or type == 'music' or type == 'video' or type == 'file'
            sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
            data = {
                'sha': sha,
                'type': type,
                'url': url
            }
            try:
                self.mysql_client.insert_one(table=settings.MEDIA_TABLE, data=data)
            except Exception as e:
                self.logging.warning(e)

    # 生成关联企业机构url队列
    def saveJiGouToRedis(self, key, value):
        self.redis_client.sadd(key=key, value=value)

    # 记录已抓取的论文
    def saveLunWenSha(self, table, sha):
        data = {
            'sha': sha
        }
        try:
            self.mysql_client.insert_one(table=table, data=data)
        except Exception as e:
            self.logging.warning('saveLunWenSha: {}'.format(e))

    # 删除任务
    def deleteLunWenUrl(self, table, sha):
        sql = "delete from {} where `sha` = '{}'".format(table, sha)
        self.mysql_client.execute(sql=sql)


class JiGouDao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        self.redis_client = redis_pool.RedisPoolUtils(config.REDIS_POOL_NUMBER)
        # self.mysql_client = mysqlpool_utils.MysqlPool(config.MYSQLPOOL_NUMBER)

    # 获取100个任务
    def getIndexUrls(self, key, lockname):
        datas = self.redis_client.queue_spops(key=key, lockname=lockname, count=100)

        return datas


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
    #         try:
    #             self.mysql_client.insert_one(table=settings.MEDIA_TABLE, data=data)
    #         except Exception as e:
    #             self.logging.warning(e)


class Dao(object):
    def __init__(self, logging):
        self.logging = logging
        self.proxy_obj = proxy.ProxyUtils(logging=logging)

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

