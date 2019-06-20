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
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from Utils import proxy
from Utils import mysqlpool_utils
from Utils import redis_pool
from Utils import timeutils


class Dao(object):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        self.logging = logging

        self.proxy_obj = proxy.ProxyUtils(logging=logging)

        if int(mysqlpool_number) == 0 or int(mysqlpool_number) < 0:
            # 默认创建一个mysql链接
            self.mysql_client = mysqlpool_utils.MysqlPool(1)
        else:
            # 创建指定个数mysql链接
            self.mysql_client = mysqlpool_utils.MysqlPool(int(mysqlpool_number))

        if int(redispool_number) == 0 or int(redispool_number) < 0:
            # 默认创建一个redis链接
            self.redis_client = redis_pool.RedisPoolUtils(1)
        else:
            # 创建指定个数redis链接
            self.redis_client = redis_pool.RedisPoolUtils(int(redispool_number))

    # 查询redis数据库中有多少任务
    def selectTaskNumber(self, key):
        return self.redis_client.scard(key=key)

    # 从Mysql获取任务
    def getNewTaskList(self, table, count):
        sql = "select * from {} where `del` = '0' limit {}".format(table, count)

        data_list = self.mysql_client.get_results(sql=sql)

        # 进入redis队列的数据，在mysql数据库中改变`del`字段值为'1'，表示正在执行
        # for data in data_list:
        #     sha = data['sha']
        #     set = {'del': '1'}
        #     self.mysql_client.update(table, data=set, where="`sha` = '{}'".format(sha))

        return data_list

    # 队列任务
    def QueueTask(self, key, data):
        if data:
            for url_data in data:
                url = url_data['memo']
                self.redis_client.sadd(key=key, value=url)

        else:
            return

    # 存储数据到Hbase数据库 resultCode
    def saveDataToHbase(self, data):
        save_data = json.dumps(data)
        url = '{}'.format(settings.SpiderDataSaveUrl)
        save_data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "python",
                "ref": "",
                "item": save_data}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        start_time = time.time()
        try:
            resp = requests.post(url=url, headers=headers, data=save_data).content.decode('utf-8')
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save data to Hbase | status: OK | memo: {} | use time: {}'.format(resp, end_time))
        except Exception as e:
            resp = e
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save data to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))

        # try:
        #     resultCode = json.loads(resp)['resultCode']
        # except:
        #     resultCode = 1
        #
        # if resultCode == 0:
        #     # 记录已存数据
        #     statistics_data = {
        #         'sha': data['sha'],
        #         'memo': str({"url": data['url']}).replace('\'', '"'),
        #         'create_at': timeutils.getNowDatetime(),
        #         'data_type': data['es']
        #     }
        #
        #     try:
        #         self.mysql_client.insert_one(table=settings.DATA_VOLUME_TOTAL_TABLE, data=statistics_data)
        #         self.mysql_client.insert_one(table=settings.DATA_VOLUME_DAY_TABLE, data=statistics_data)
        #
        #     except:
        #         return resp

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
                "item": json.dumps(item)
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        start_time = time.time()
        try:
            resp = requests.post(url=url, headers=headers, data=data).content.decode('utf-8')
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save media to Hbase | status: OK | memo: {} | use time: {}'.format(resp, end_time))
        except Exception as e:
            resp = e
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save media to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))

        # try:
        #     resultCode = json.loads(resp)['resultCode']
        # except:
        #     resultCode = 1
        #
        # if resultCode == 0:
        #     # 记录已存数据
        #     statistics_data = {
        #         'sha': sha,
        #         'create_at': timeutils.getNowDatetime(),
        #         'type': type
        #     }
        #     try:
        #         self.mysql_client.insert_one(table=settings.STATISTICS_TABLE, data=statistics_data)
        #
        #     except:
        #         return resp
        #
        # return resp

    # TODO 保存数据到mysql，不再使用
    def saveDataToMysql(self, table, data):
        try:
            self.mysql_client.insert_one(table=table, data=data)
        except Exception as e:
            self.logging.warning('保存数据到mysql警告: {}'.format(e))

    # TODO 保存媒体文件链接到mysql，不再使用
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
                self.logging.warning('保存媒体链接到mysql警告: {}'.format(e))

    # 数据库记录爬虫名
    def saveSpiderName(self, name):
        # 查询爬虫是否存在
        sha = hashlib.sha1(name.encode('utf-8')).hexdigest()
        select_sql = "select * from {} where sha = '{}'".format(settings.SPIDER_TABLE, sha)
        spider_status = self.mysql_client.get_results(sql=select_sql)
        if spider_status:
            # 有
            return
        else:
            # 没有
            memo = {
                'sha': sha,
                'name': name
            }
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '\"'),
                'data_type': name,
                'create_at': timeutils.getNowDatetime()
            }
            try:
                self.mysql_client.insert_one(table=settings.SPIDER_TABLE, data=data)
            except Exception as e:
                print(e)

    # 判断任务是否抓取过
    def getTaskStatus(self, sha):
        sql = "select * from {} where `sha` = '{}'".format(settings.DATA_VOLUME_TOTAL_TABLE, sha)
        status = self.mysql_client.get_results(sql=sql)
        if status:

            return True
        else:

            return False

    # 保存任务
    def saveTask(self, data, cateid):
        table = 'ss_task'
        sha = data['sha']

        save_data = {
            'sha': sha,
            'memo': str(data).replace('\'', '"'),
            'cateid': cateid
        }

        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)

        if not data_status:
            # 插入
            try:
                self.mysql_client.insert_one(table=table, data=save_data)
                self.logging.info('insert data complete: {}'.format(sha))
            except Exception as e:

                self.logging.error('insert data error: {}'.format(e))

        else:
            # 更新
            try:
                self.mysql_client.update(table=table, data=save_data, where="sha = '{}'".format(sha))

                self.logging.info('update data complete: {}'.format(sha))
                return json.dumps({"status": 0, "sha": sha})

            except Exception as e:
                self.logging.error('uodate data error: {}'.format(e))

    # 获取任务
    def getTask(self, key, count, lockname):
        return self.redis_client.queue_spops(key=key, count=count, lockname=lockname)
