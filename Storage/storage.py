# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import base64
from PIL import Image
from io import BytesIO
import hashlib
import requests
import re
import time
import ast

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

    # 种子任务存入Mysql数据库
    def saveTaskToMysql(self, table, memo, ws, es):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        ctx = json.dumps(memo, ensure_ascii=False)  # 参数防止中文字符串变成Unicode字节码
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        # 如果没有，直接存入数据库
        if not data_status:
            data = {
                'sha': sha,
                'ctx': ctx,
                'url': url,
                'es': es,
                'ws': ws,
                'date_created': timeutils.getNowDatetime()
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info('已存储种子: {}'.format(url))
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('种子已存在: {}'.format(sha))
            # # 从mysql数据库中取出该种子
            # result = self.getOneTask(table, sha)
            # oldCtx = ast.literal_eval(result[0]['ctx'])
            # # 遍历新ctx中的key,value值
            # for k,v in memo.items():
            #     # 遍历旧的key,value值
            #     for m,n in oldCtx.items():
            #         # 判断新的key值是否以's_'开头，并且value是字符串
            #         if k.startswith('s_') and isinstance(v, str):
            #             if k == m:
            #                 if v not in n:
            #                     oldCtx[k] = n + '|' + v
            #                     break
            #                 else:
            #                     break
            #             else:
            #                 continue
            #         else:
            #             if k == m:
            #                 oldCtx[k] = v
            #                 break
            #             else:
            #                 continue
            #     else:
            #         oldCtx[k] = v
            # print(oldCtx)
            #
            # # 删除原数据库种子
            # self.deleteTask(table=table, sha=sha)
            # # 存储新种子
            # rCtx = json.dumps(oldCtx, ensure_ascii=False)
            # newdata = {
            #     'sha': sha,
            #     'ctx': rCtx,
            #     'url': url,
            #     'es': es,
            #     'ws': ws,
            #     'date_created': timeutils.getNowDatetime()
            # }
            # try:
            #     self.mysql_client.insert_one(table=table, data=newdata)
            #     self.logging.info('已存储种子: {}'.format(url))
            # except Exception as e:
            #     self.logging.warning('数据存储警告: {}'.format(e))

    # 从Mysql获取指定一条任务
    def getOneTask(self, table, sha):
        sql = "select * from {} where `del` = '0' and `sha` = '{}'".format(table, sha)

        data_list = self.mysql_client.get_results(sql=sql)

        self.logging.info('种子已存在, 需取出做附加信息合并，再存储该种子: {}'.format(sha))

        return data_list

    # 从Mysql获取任务
    def getNewTaskList(self, table, ws, es, count):
        sql = "select * from {} where `del` = '0' and `ws` = '{}' and `es` = '{}' limit {}".format(table, ws, es, count)

        data_list = self.mysql_client.get_results(sql=sql)

        self.logging.info('已从Mysql获取到{}个任务'.format(len(data_list)))

        # 进入redis队列的数据，在mysql数据库中改变`del`字段值为'1'，表示正在执行
        # for data in data_list:
        #     sha = data['sha']
        #     set = {'del': '1'}
        #     self.mysql_client.update(table, data=set, where="`sha` = '{}'".format(sha))

        return data_list

    # 队列种子任务
    def QueueJobTask(self, key, data):
        if data:
            for url in data:
                self.redis_client.sadd(key=key, value=str(url))
            self.logging.info('已队列 {} 条种子'.format(len(data)))

        else:
            return

    # 队列一条种子任务
    def QueueOneTask(self, key, data):
        if data:
            self.redis_client.sadd(key=key, value=str(data))
            self.logging.info('已队列1条种子')

        else:
            return

    # 从mysql队列任务到redis
    def QueueTask(self, key, data):
        if data:
            for url_data in data:
                url = url_data['ctx']
                self.redis_client.sadd(key=key, value=url)

            self.logging.info('已成功向redis队列{}个任务'.format(len(data)))

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
            respon = ast.literal_eval(resp)
            if respon['resultCode'] == 0:
                end_time = int(time.time() - start_time)
                self.logging.info('title: Save data to Hbase | status: OK | memo: {} | use time: {}'.format(resp, end_time))
                return True
            else:
                end_time = int(time.time() - start_time)
                self.logging.info('title: Save data to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))
                return False
        except Exception as e:
            resp = e
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save data to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))
            return False

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
    def saveMediaToHbase(self, media_url, content, item, type):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        # 二进制图片文件转成base64文件
        content_bs64 = base64.b64encode(content)
        # 解码base64图片文件
        dbs = base64.b64decode(content_bs64)
        # 内存中打开图片
        img = Image.open(BytesIO(content))
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
        # item = {
        #     'pk': sha,
        #     'type': type,
        #     'url': media_url,
        #     'biz_title':
        #     'length': "{}".format(len(dbs)),
        #     'natural_height': str(img['height']),
        #     'natural_width': str(img['width']),
        #     'rel_esse':
        #
        # }
        item['relEsse'] = str(item['relEsse'])
        item['relPics'] = str(item['relPics'])
        item['pk'] = sha
        item['type'] = type
        item['url'] = media_url
        item['tagSrc'] = media_url
        item['length'] = "{}".format(len(dbs))
        item['naturalHeight'] = "{}".format(img.height)
        item['naturalWidth'] = "{}".format(img.width)
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "100",
                "content": "{}".format(content_bs64.decode('utf-8')),
                # "content": "{}".format(content_bs64),
                "ref": "",
                "item": json.dumps(item)
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        start_time = time.time()
        try:
            resp = requests.post(url=url, headers=headers, data=data).content.decode('utf-8')
            respon = ast.literal_eval(resp)
            if respon['resultCode'] == 0:
                end_time = int(time.time() - start_time)
                self.logging.info('title: Save media to Hbase | status: OK | memo: {} | use time: {}'.format(resp, end_time))
                return True
            else:
                end_time = int(time.time() - start_time)
                self.logging.info('title: Save media to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))
                return False
        except Exception as e:
            resp = e
            end_time = int(time.time() - start_time)
            self.logging.info('title: Save media to Hbase | status: NO | memo: {} | use time: {}'.format(resp, end_time))
            return False

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
        select_sql = "select * from {} where `sha` = '{}'".format(settings.SPIDER_TABLE, sha)
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

    # 物理删除任务
    def deleteTask(self, table, sha):
        sql = "delete from {} where `sha` = '{}' and `del` = '0'".format(table, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('任务已删除: {}'.format(sha))
        except:
            self.logging.warning('任务删除异常: {}'.format(sha))

    # 逻辑删除任务
    def deleteLogicTask(self, table, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=table, data=data, where="sha = '{}'".format(sha))
            self.logging.info('任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('任务逻辑删除异常: {}'.format(sha))
