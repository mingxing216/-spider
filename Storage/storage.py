# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import base64
import random
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

        self.s = requests.Session()

        self.proxy_obj = proxy.ProxyUtils(logging=logging)
        # 获取本机IP，存储使用
        while True:
            if self.proxy_obj.getLocalIP():
                self.localIP =self.proxy_obj.getLocalIP()
                break
            else:
                continue

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

    def saveTaskToMysql(self, table, memo, ws, es):
        start_time = time.time()
        self.logging.info('开始存储种子')
        ret = self.__saveTaskToMysql(table, memo, ws, es)
        if ret:
            self.logging.info('handle | 种子存储成功 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 种子存储失败 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        self.logging.info('结束存储种子')
        return ret

    # 种子任务存入Mysql数据库
    def __saveTaskToMysql(self, table, memo, ws, es):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        memo['sha'] = sha
        ctx = json.dumps(memo, ensure_ascii=False)  # 参数防止中文字符串变成Unicode字节码
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        # print(data_status)
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
                return True

            except Exception as e:
                self.logging.warning('种子存储警告: {}'.format(ctx))
                return False

        else:
            # self.logging.warning('种子已存在: {}'.format(sha))
            # 从mysql数据库中取出该种子
            if ctx == data_status['ctx']:
                self.logging.warning('种子已存在: {}'.format(sha))
                return True

            else:
                oldCtx = json.loads(data_status['ctx'])
                # 遍历新ctx中的key,value值
                for k,v in memo.items():
                    # 遍历旧的key,value值
                    for m,n in oldCtx.items():
                        # 判断新的key值是否以's_'开头，并且value是字符串
                        if k.startswith('s_') and isinstance(v, str):
                            if k == m:
                                if v not in n:
                                    if n == '':
                                        oldCtx[k] = v
                                    else:
                                        oldCtx[k] = n + '|' + v
                                    break
                                else:
                                    break
                            else:
                                continue
                        else:
                            if k == m:
                                oldCtx[k] = v
                                break
                            else:
                                continue
                    else:
                        oldCtx[k] = v
                # print(oldCtx)

                # 存储新种子
                rCtx = json.dumps(oldCtx, ensure_ascii=False)
                newdata = {
                    'sha': sha,
                    'ctx': rCtx,
                    'url': url,
                    'es': es,
                    'ws': ws,
                    'date_created': timeutils.getNowDatetime()
                }
                try:
                    self.mysql_client.update(table=table, data=newdata, where="`sha` = '{}'".format(sha))
                    self.logging.info('已更新种子: {}'.format(url))
                    return True

                except Exception as e:
                    self.logging.warning('种子更新警告: {}'.format(ctx))
                    return False

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
                self.redis_client.sadd(key=key, value=json.dumps(url, ensure_ascii=False))
            self.logging.info('已队列 {} 条种子'.format(len(data)))

        else:
            return

    # 队列一条种子任务
    def QueueOneTask(self, key, data):
        if data:
            self.redis_client.sadd(key=key, value=json.dumps(data, ensure_ascii=False))
            self.logging.info('已队列1条种子')

        else:
            return

    # # 从mysql队列任务到redis
    # def QueueTask(self, key, data):
    #     if data:
    #         for url_data in data:
    #             url = url_data['ctx']
    #             self.redis_client.sadd(key=key, value=url)
    #
    #         self.logging.info('已成功向redis队列{}个任务'.format(len(data)))
    #
    #     else:
    #         return

    # 从mysql队列任务到redis
    def QueueTask(self, key, data):
        if data:
            for url_data in data:
                sha = url_data['sha']
                json_ctx = json.loads(url_data['ctx'])
                json_ctx['sha'] = sha
                url = json.dumps(json_ctx, ensure_ascii=False)

                self.redis_client.sadd(key=key, value=url)

            self.logging.info('已成功向redis队列{}个任务'.format(len(data)))

        else:
            return

    def saveDataToHbase(self, data):
        start_time = time.time()
        self.logging.info('开始存储实体')
        ret = self.__saveDataToHbase(data)
        if ret:
            self.logging.info('handle | 存储实体成功 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 存储实体失败 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        self.logging.info('结束存储实体')
        return ret

    # 存储数据到Hbase数据库 resultCode
    def __saveDataToHbase(self, data):
        save_data = json.dumps(data, ensure_ascii=False)
        # 将待存储数据编码成二进制数据
        b_data = save_data.encode('utf-8')
        url = '{}'.format(settings.SpiderDataSaveUrl)
        form_data = {"ip": "{}".format(self.localIP),
                     "wid": "python",
                     "ref": "",
                     "item": save_data}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        # 重试次数
        count = 0
        while True:
            start_time = time.time()
            try:
                resp = requests.post(url=url, headers=headers, data=form_data, timeout=(5, 5)).content.decode('utf-8')
                respon = ast.literal_eval(resp)
                if respon['resultCode'] == 0:
                    self.logging.info('handle | Save data to Hbase | use time: {}s | status: OK | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), data.get('sha'), len(b_data), resp))
                    return True

                else:
                    if count >= 2:
                        self.logging.warning('handle | Save data to Hbase | use time: {}s | status: NO | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), data.get('sha'), len(b_data), resp))
                        return False
                    else:
                        count += 1
                        self.logging.warning('handle | Save data to Hbase again ... | use time: {}s | sha: {} | memo: {}'.format('%.3f' %(time.time() - start_time), data.get('sha'), resp))
                        time.sleep(1)
                        continue

            except Exception as e:
                if count >= 2:
                    self.logging.error('handle | Save data to Hbase | use time: {}s | status: NO | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), data.get('sha'), len(b_data), e))
                    return False
                else:
                    count += 1
                    self.logging.warning('handle | Save data to Hbase again ... | use time: {}s | sha: {} | memo: {}'.format('%.3f' %(time.time() - start_time), data.get('sha'), e))
                    time.sleep(1)
                    continue

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

    def saveMediaToHbase(self, media_url, content, item, type):
        start_time = time.time()
        self.logging.info('开始存储附件')
        ret = self.__saveMediaToHbase(media_url, content, item, type)
        if ret:
            self.logging.info('handle | 存储附件成功 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 存储附件失败 | use time: {}s'.format('%.3f' % (time.time() - start_time)))
        self.logging.info('结束存储附件')

        return ret

    # 保存流媒体到hbase
    def __saveMediaToHbase(self, media_url, content, item, type):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        # # 二进制图片文件转成base64文件
        content_bs64 = base64.b64encode(content)
        # content_bs64 = content
        # 解码base64图片文件为二进制文件
        dbs = base64.b64decode(content_bs64)
        # 内存中打开图片
        img = Image.open(BytesIO(content))
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
        # sha = int(random.random()*10000000000000000)

        data_dict = {
            'pk': sha,
            'type': type,
            'url': media_url,
            'biz_title': item.get('bizTitle'),
            'rel_esse': str(item.get('relEsse')),
            'rel_pics': str(item.get('relPics')),
            'length': "{}".format(len(dbs)),
            'tag_src': media_url,
            'natural_height': "{}".format(img.height),
            'natural_width': "{}".format(img.width)
        }

        form_data = {
            "ip": "{}".format(self.localIP),
            "wid": "100",
            'url': media_url,
            "content": "{}".format(content_bs64.decode('utf-8')),
            # "content": "{}".format(content),
            # "content": "{}".format(content_bs64),
            'type': type,
            "ref": "",
            "item": json.dumps(data_dict, ensure_ascii=False)
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        # 重试次数
        count = 0
        while True:
            start_time = time.time()
            try:
                resp = self.s.post(url=url, headers=headers, data=form_data, timeout=(5, 5)).content.decode('utf-8')
                respon = ast.literal_eval(resp)
                if respon['resultCode'] == 0:
                    self.logging.info('handle | Save media to Hbase | use time: {}s | status: OK | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), sha, data_dict['length'], resp))
                    return True

                else:
                    if count >= 2:
                        self.logging.warning('handle | Save media to Hbase | use time: {}s | status: NO | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), sha, data_dict['length'], resp))
                        return False
                    else:
                        count += 1
                        self.logging.warning('handle | Save media to Hbase again ... | use time: {}s | sha: {} | memo: {}'.format('%.3f' %(time.time() - start_time), sha, resp))
                        time.sleep(1)
                        continue

            except Exception as e:
                if count >= 2:
                    self.logging.error('handle | Save media to Hbase | use time: {}s | status: NO | sha: {} | length: {} | memo: {}'.format('%.3f' %(time.time() - start_time), sha, data_dict['length'], e))
                    return False
                else:
                    count += 1
                    # print(e)
                    self.logging.warning('handle | Save media to Hbase again ... | use time: {}s | sha: {} | memo: {}'.format('%.3f' %(time.time() - start_time), sha, e))
                    time.sleep(1)
                    continue

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

    def getTask(self, key, count, lockname):
        start_time = time.time()
        ret = self._getTask(key, count, lockname)
        self.logging.info('handle | 获取 {} 条任务 | use time: {}s'.format(len(ret), '%.3f' % (time.time() - start_time)))
        return ret

    # 从redis队列中获取任务
    def _getTask(self, key, count, lockname):
        return self.redis_client.queue_spops(key=key, count=count, lockname=lockname)

    def deleteTask(self, table, sha=None, url=None):
        start_time = time.time()
        self.__deleteTask(table, sha, url)
        self.logging.info('handle | 删除任务 | use time: {}s'.format('%.3f' % (time.time() - start_time)))

    # 物理删除mysql中任务
    def __deleteTask(self, table, sha=None, url=None):
        if sha:
            try:
                sql = "delete from {} where `sha` = '{}' and `del` = '0'".format(table, sha)
                self.mysql_client.execute(sql=sql)
                self.logging.info('任务已删除: {}'.format(sha))
            except:
                self.logging.warning('任务删除异常: {}'.format(sha))

        elif url:
            try:
                sql = "delete from {} where `url` = '{}' and `del` = '0'".format(table, url)
                self.mysql_client.execute(sql=sql)
                self.logging.info('任务已删除: {}'.format(url))
            except:
                self.logging.warning('任务删除异常: {}'.format(url))

    def deleteLogicTask(self, table, sha=None, url=None):
        start_time = time.time()
        self.__deleteLogicTask(table, sha, url)
        self.logging.info('handle | 逻辑删除任务 | use time: {}s'.format('%.3f' % (time.time() - start_time)))

    # 逻辑删除mysql中任务
    def __deleteLogicTask(self, table, sha=None, url=None):
        data = {
            'del': '1'
        }
        if sha:
            try:
                self.mysql_client.update(table=table, data=data, where="`sha` = '{}' and `del` = '0'".format(sha))
                self.logging.info('任务已逻辑删除: {}'.format(sha))
            except:
                self.logging.warning('任务逻辑删除异常: {}'.format(sha))

        elif url:
            try:
                self.mysql_client.update(table=table, data=data, where="url = '{}' and `del` = '0'".format(url))
                self.logging.info('任务已逻辑删除: {}'.format(url))
            except:
                self.logging.warning('任务逻辑删除异常: {}'.format(url))

    def finishTask(self, table, sha=None, url=None):
        start_time = time.time()
        self.__finishTask(table, sha, url)
        self.logging.info('handle | 任务已完成 | use time: {}s'.format('%.3f' % (time.time() - start_time)))

    # mysql中已完成任务
    def __finishTask(self, table, sha=None, url=None):
        data = {
            'del': '2'
        }
        if sha:
            try:
                self.mysql_client.update(table=table, data=data, where="`sha` = '{}' and `del` = '0'".format(sha))
                self.logging.info('任务已完成: {}'.format(sha))
            except:
                self.logging.warning('已完成任务标记异常: {}'.format(sha))

        elif url:
            try:
                self.mysql_client.update(table=table, data=data, where="url = '{}' and `del` = '0'".format(url))
                self.logging.info('任务已完成: {}'.format(url))
            except:
                self.logging.warning('已完成任务标记异常: {}'.format(url))
