# -*- coding:utf-8- *-

"""

"""
import sys
import os
import json
import base64
from PIL import Image
from io import BytesIO
import hashlib
import requests
import re
from requests.adapters import HTTPAdapter
from urllib3 import Retry

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from ProxyPool.ProxyClient.proxy_client import ProxyPoolClient
from Utils import mysql_pool, redis_pool, timers, timeutils


class Dao(object):
    def __init__(self, logging, host, port, user, pwd, db, mysqlpool_number=0, redispool_number=0):
        self.logging = logging
        self.timer = timers.Timer()
        self.s = requests.Session()
        # 连接主机数、最大连接数、最大重试次数
        self.s.mount('http://', HTTPAdapter(pool_connections=2, pool_maxsize=32,
                                            max_retries=Retry(total=2, method_whitelist=frozenset(['GET', 'POST']))))
        self.s.mount('https://', HTTPAdapter(pool_connections=2, pool_maxsize=32,
                                             max_retries=Retry(total=2, method_whitelist=frozenset(['GET', 'POST']))))
        self.s.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}
        # 获取本机IP，存储使用
        while True:
            local_ip = ProxyPoolClient.get_local_ip()
            if not local_ip:
                continue
            else:
                self.local_ip = '{}'.format(local_ip)
                break

        if int(mysqlpool_number) == 0 or int(mysqlpool_number) < 0:
            # 默认创建一个mysql链接
            self.mysql_client = mysql_pool.MysqlPool(number=1, host=host, port=port, user=user, pwd=pwd, db=db,
                                                     logger=logging)
        else:
            # 创建指定个数mysql链接
            self.mysql_client = mysql_pool.MysqlPool(number=int(mysqlpool_number), host=host, port=port, user=user,
                                                     pwd=pwd, db=db, logger=logging)

        if int(redispool_number) == 0 or int(redispool_number) < 0:
            # 默认创建一个redis链接
            self.redis_client = redis_pool.RedisPoolUtils(1)
        else:
            # 创建指定个数redis链接
            self.redis_client = redis_pool.RedisPoolUtils(int(redispool_number))

    # 查询redis数据库中有多少任务
    def select_task_number(self, key):
        return self.redis_client.scard(key=key)

    def save_task_to_mysql(self, table, memo, ws, es, msg='NULL'):
        self.timer.start()
        self.logging.info('mysql start | 开始存储种子')
        ret = self.__save_task_to_mysql(table, memo, ws, es, msg)
        if ret:
            self.logging.info('mysql end | 种子存储成功 | use time: {}'.format(self.timer.use_time()))
        else:
            self.logging.error('mysql end | 种子存储失败 | use time: {}'.format(self.timer.use_time()))
        return ret

    # 种子任务存入Mysql数据库
    def __save_task_to_mysql(self, table, memo, ws, es, msg='NULL'):
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
                'msg': msg,
                'date_created': timeutils.get_now_datetime()
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info('mysql | 已存储种子: {}'.format(url))
                return True

            except Exception as e:
                self.logging.warning('mysql | 种子存储警告: {}, {}'.format(e, ctx))
                return False

        else:
            # self.logging.warning('种子已存在: {}'.format(sha))
            # 从mysql数据库中取出该种子
            if ctx == data_status['ctx']:
                self.logging.warning('mysql | 种子已存在: {}'.format(sha))
                return True

            else:
                old_ctx = json.loads(data_status['ctx'])
                # 遍历新ctx中的key,value值
                for k, v in memo.items():
                    # 遍历旧的key,value值
                    for m, n in old_ctx.items():
                        # 判断新的key值是否以's_'开头，并且value是字符串
                        if k.startswith('s_') and isinstance(v, str):
                            if k == m:
                                if v not in n:
                                    if n == '':
                                        old_ctx[k] = v
                                    else:
                                        old_ctx[k] = n + '|' + v
                                    break
                                else:
                                    break
                            else:
                                continue
                        else:
                            if k == m:
                                old_ctx[k] = v
                                break
                            else:
                                continue
                    else:
                        old_ctx[k] = v
                # print(old_ctx)

                # 存储新种子
                new_ctx = json.dumps(old_ctx, ensure_ascii=False)
                newdata = {
                    'sha': sha,
                    'ctx': new_ctx,
                    'url': url,
                    'es': es,
                    'ws': ws,
                    'msg': msg,
                    'date_created': timeutils.get_now_datetime()
                }
                try:
                    self.mysql_client.update(table=table, data=newdata, where="`sha` = '{}'".format(sha))
                    self.logging.info('mysql | 已更新种子: {}'.format(url))
                    return True

                except Exception as e:
                    self.logging.warning('mysql | 种子更新警告: {}, {}'.format(e, ctx))
                    return False

    # 更新mysql种子状态
    def update_task_to_mysql(self, table, data, sha):
        self.timer.start()
        self.logging.info('mysql start | 开始更新种子')
        ret = self.__update_task_to_mysql(table, data, sha)
        if ret:
            self.logging.info('mysql end | 种子更新成功 | use time: {}'.format(self.timer.use_time()))
        else:
            self.logging.error('mysql end | 种子更新失败 | use time: {}'.format(self.timer.use_time()))
        return ret

    # 种子任务存入Mysql数据库
    def __update_task_to_mysql(self, table, data, sha):
        try:
            self.mysql_client.update(table=table, data=data, where="`sha` = '{}'".format(sha))
            self.logging.info('mysql | 已更新种子: {}'.format(sha))
            return True

        except Exception as e:
            self.logging.warning('mysql | 种子更新警告: {}, {}'.format(e, sha))
            return False

    # 从Mysql获取指定一条任务
    def get_one_task_from_mysql(self, table, sha):
        self.timer.start()
        sql = "select * from {} where `sha` = '{}' and `del` = '0'".format(table, sha)

        data_list = self.mysql_client.get_results(sql=sql)

        self.logging.info('mysql | 种子已存在, 需取出做附加信息合并，再存储该种子: {} | use time: {}'.format(sha, self.timer.use_time()))

        return data_list

    # 从Mysql获取任务
    def get_task_list_from_mysql(self, table, ws, es, count):
        self.timer.start()
        sql = "select * from {} where `ws` = '{}' and `es` = '{}' and `del` = '0' limit {}".format(table, ws, es, count)

        data_list = self.mysql_client.get_results(sql=sql)

        self.logging.info('mysql | 已从Mysql获取到{}个任务 | use time: {}'.format(len(data_list), self.timer.use_time()))

        # 进入redis队列的数据，在mysql数据库中改变`del`字段值为'1'，表示正在执行
        # for data in data_list:
        #     sha = data['sha']
        #     set = {'del': '1'}
        #     self.mysql_client.update(table, data=set, where="`sha` = '{}'".format(sha))

        return data_list

    # 队列种子任务
    def queue_tasks_to_redis(self, key, data):
        self.timer.start()
        if data:
            for url in data:
                self.redis_client.sadd(key=key, value=json.dumps(url, ensure_ascii=False))
            self.logging.info('task | 已队列 {} 条种子 | use time: {}'.format(len(data), self.timer.use_time()))

        else:
            return

    # 队列一条种子任务
    def queue_one_task_to_redis(self, key, data):
        self.timer.start()
        if data:
            self.redis_client.sadd(key=key, value=json.dumps(data, ensure_ascii=False))
            self.logging.info('task | 已队列 1 条种子 | use time: {}'.format(self.timer.use_time()))

        else:
            return

    # 队列一条种子任务
    def remove_one_task_from_redis(self, key, data):
        self.timer.start()
        if data:
            self.redis_client.srem(key=key, value=json.dumps(data, ensure_ascii=False))
            self.logging.info('task | 已删除队列中 1 条种子 | use time: {}'.format(self.timer.use_time()))

        else:
            return

    # 从mysql队列任务到redis
    def queue_tasks_from_mysql_to_redis(self, key, data):
        self.timer.start()
        if data:
            for url_data in data:
                sha = url_data['sha']
                json_ctx = json.loads(url_data['ctx'])
                json_ctx['sha'] = sha
                url = json.dumps(json_ctx, ensure_ascii=False)

                self.redis_client.sadd(key=key, value=url)

            self.logging.info('task | 已成功向redis队列 {} 个任务 | use time: {}'.format(len(data), self.timer.use_time()))

        else:
            return

    def save_data_to_hbase(self, data):
        self.timer.start()
        self.logging.info('storage start | 开始存储实体')
        ret = self.__save_data_to_hbase(data)
        if ret:
            self.logging.info('storage end | 存储实体成功 | use time: {}'.format(self.timer.use_time()))
        else:
            self.logging.error('storage end | 存储实体失败 | use time: {}'.format(self.timer.use_time()))
        return ret

    # 存储数据到Hbase数据库 resultCode
    def __save_data_to_hbase(self, data_list):
        save_data = json.dumps(data_list, ensure_ascii=False)
        # 将待存储数据编码成二进制数据
        url = settings.SAVE_HBASE_DATA_URL
        form_data = {'ip': self.local_ip,
                     'wid': 'python',
                     'ref': '',
                     'list': save_data}

        # 开始存储实体数据
        data_start = timers.Timer()
        data_start.start()
        try:
            resp = self.s.post(url=url, data=form_data, timeout=(5, 10)).content.decode('utf-8')
            respon = json.loads(resp)
            if respon['resultCode'] == 0:
                for data in data_list:
                    self.logging.info(
                        'storage | Save data to Hbase | use time: {} | status: OK | sha: {} | ss: {} | memo: {}'.format(
                            data_start.use_time(), data.get('sha'), data.get('ss'), resp))
                return True

            else:
                for data in data_list:
                    self.logging.error(
                        'storage | Save data to Hbase | use time: {} | status: NO | sha: {} | ss: {} | memo: {}'.format(
                            data_start.use_time(), data.get('sha'), data.get('ss'), resp))
                return False

        except Exception as e:
            for data in data_list:
                entity_data = json.dumps(data, ensure_ascii=False)
                b_data = entity_data.encode('utf-8')
                self.logging.error(
                    'storage | Save data to Hbase | use time: {} | status: NO | sha: {} | length: {} | memo: {}'.format(
                        data_start.use_time(), data.get('sha'), len(b_data), e))
            return False

    def save_media_to_hbase(self, media_url, content, item, type, length=None, contype=None):
        self.timer.start()
        self.logging.info('storage start | 开始存储附件 {}'.format(type))
        ret = self.__save_media_to_hbase(media_url, content, item, type, length, contype)
        if ret:
            self.logging.info('storage end | 存储附件成功 {} | use time: {}'.format(type, self.timer.use_time()))
        else:
            self.logging.error('storage end | 存储附件失败 {} | use time: {}'.format(type, self.timer.use_time()))

        return ret

    # 保存流媒体到hbase
    def __save_media_to_hbase(self, media_url, content, item, type, length=None, contype=None):
        url = settings.SAVE_HBASE_MEDIA_URL
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()

        data_dict = {
            'pk': sha,
            'type': type,
            'url': media_url,
            'biz_title': item.get('title'),
            'rel_esse': json.dumps(item.get('rel_esse'), ensure_ascii=False),
            'rel_pics': json.dumps(item.get('rel_pics'), ensure_ascii=False),
            'content_type': contype,
            'tag_src': media_url,
            'metadata_version': 'V1.2'
        }
        store_data = ''
        # 图片存储
        if 'image' in contype:
            # 二进制图片文件转成base64文件
            content_bs64 = base64.b64encode(content)
            length = len(content)
            # 内存中打开图片
            img = Image.open(BytesIO(content))
            data_dict['natural_height'] = "{}".format(img.height)
            data_dict['natural_width'] = "{}".format(img.width)
            data_dict['length'] = length
            store_data = content_bs64.decode('utf-8')
        # 文档存储
        if 'pdf' in contype:
            # 二进制文件转成base64文件
            content_bs64 = base64.b64encode(content)
            data_dict['length'] = length
            store_data = content_bs64.decode('utf-8')
        # HTML数据存储
        if 'text' in contype:
            store_data = content
            length = len(content)
            data_dict['length'] = length

        form_data = {
            'ip': self.local_ip,
            'type': type,
            'url': media_url,
            'content': store_data,
            'wid': '100',
            'ref': '',
            'item': json.dumps(data_dict, ensure_ascii=False)
        }
        # 开始存储多媒体数据
        media_start = timers.Timer()
        media_start.start()
        try:
            resp = self.s.post(url=url, data=form_data, timeout=(10, 20)).content.decode('utf-8')
            respon = json.loads(resp)
            if respon['resultCode'] == 0:
                self.logging.info(
                    'storage | Save media to Hbase | use time: {} | status: OK | sha: {} | length: {} | memo: {}'.format(
                        media_start.use_time(), sha, data_dict.get('length', ''), resp))
                return True

            else:
                self.logging.error(
                    'storage | Save media to Hbase | use time: {} | status: NO | sha: {} | length: {} | memo: {}'.format(
                        media_start.use_time(), sha, data_dict.get('length', ''), resp))
                return False

        except Exception as e:
            self.logging.error(
                'storage | Save media to Hbase | use time: {} | status: NO | sha: {} | length: {} | memo: {}'.format(
                    media_start.use_time(), sha, data_dict.get('length', ''), e))
            return False

    # 读取Hbase实体数据
    def get_data_from_hbase(self, sha, ss):
        # 获取接口
        url = settings.GET_HBASE_DATA_URL.format(sha, ss)
        # 开始获取实体数据
        self.timer.start()
        try:
            resp = self.s.get(url=url, timeout=(10, 30))
            if resp:
                if resp.status_code == 200:
                    self.logging.info('storage | Get data from Hbase | use time: {} | status: {} | sha: {}'.format(
                        self.timer.use_time(), resp.status_code, sha))
                    return resp.json()

                else:
                    self.logging.warning('storage | Get data from Hbase | use time: {} | status: {} | sha: {}'.format(
                        self.timer.use_time(), resp.status_code, sha))
                    return

        except requests.exceptions.RequestException as e:
            self.logging.error('storage | Get data from Hbase | use time: {} | status: NO | sha: {} | memo: {}'.format(
                self.timer.use_time(), sha, e))
            return

    # 读取Hbase多媒体数据
    def get_media_from_hbase(self, sha, ss):
        # 获取接口
        url = settings.GET_HBASE_MEDIA_URL.format(sha, ss)
        # 开始获取实体数据
        self.timer.start()
        try:
            resp = self.s.get(url=url, timeout=(10, 300))
            if resp:
                if resp.status_code == 200:
                    self.logging.info('storage | Get media from Hbase | use time: {} | status: {} | sha: {}'.format(
                        self.timer.use_time(), resp.status_code, sha))
                    return resp.json()

                else:
                    self.logging.warning('storage | Get media from Hbase | use time: {} | status: {} | sha: {}'.format(
                        self.timer.use_time(), resp.status_code, sha))
                    return

        except requests.exceptions.RequestException as e:
            self.logging.error(
                'storage | Get media from Hbase | use time: {} | status: NO | sha: {} | memo: {}'.format(
                    self.timer.use_time(), sha, e))
            return

    # TODO 保存数据到mysql，不再使用
    def save_data_to_mysql(self, table, data):
        try:
            self.mysql_client.insert_one(table=table, data=data)
        except Exception as e:
            self.logging.warning('保存数据到mysql警告: {}'.format(e))

    # TODO 保存媒体文件链接到mysql，不再使用
    def save_media_to_mysql(self, url, type):
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
    def save_spider_name(self, name):
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
                'create_at': timeutils.get_now_datetime()
            }
            try:
                self.mysql_client.insert_one(table=settings.SPIDER_TABLE, data=data)
            except Exception as e:
                print(e)

    # 判断任务是否抓取过
    def get_task_status(self, sha):
        sql = "select * from {} where `sha` = '{}'".format(settings.DATA_VOLUME_TOTAL_TABLE, sha)
        status = self.mysql_client.get_results(sql=sql)
        if status:
            return True

        else:
            return False

    # 保存任务
    def save_task(self, data, cateid):
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
                self.logging.info('mysql | insert data complete: {}'.format(sha))
            except Exception as e:

                self.logging.error('mysql | insert data error: {}'.format(e))

        else:
            # 更新
            try:
                self.mysql_client.update(table=table, data=save_data, where="sha = '{}'".format(sha))

                self.logging.info('mysql | update data complete: {}'.format(sha))
                return json.dumps({"status": 0, "sha": sha})

            except Exception as e:
                self.logging.error('update data error: {}'.format(e))

    def get_one_task_from_redis(self, key, lockname=None):
        self.timer.start()
        ret = self._get_one_task_from_redis(key, lockname)
        if ret is not None:
            self.logging.info('task | 获取 1 条任务 | use time: {}'.format(self.timer.use_time()))
            return ret

    # 从redis队列中获取1条任务
    def _get_one_task_from_redis(self, key, lockname=None):
        return self.redis_client.queue_spop(key=key, lockname=lockname)

    def get_task_from_redis(self, key, count, lockname=None):
        self.timer.start()
        ret = self._get_task_from_redis(key, count, lockname)
        if len(ret) > 0:
            self.logging.info('task | 获取 {} 条任务 | use time: {}'.format(len(ret), self.timer.use_time()))
            return ret

    # 从redis队列中获取任务
    def _get_task_from_redis(self, key, count, lockname=None):
        return self.redis_client.queue_spops(key=key, count=count, lockname=lockname)

    def delete_task_from_mysql(self, table, sha=None, url=None):
        self.timer.start()
        self._delete_task_from_mysql(table, sha, url)
        self.logging.info('mysql end | 数据库删除任务 | use time: {}'.format(self.timer.use_time()))

    # 物理删除mysql中任务
    def _delete_task_from_mysql(self, table, sha=None, url=None):
        if sha:
            try:
                sql = "delete from {} where `sha` = '{}' and `del` = '0'".format(table, sha)
                self.mysql_client.get_result(sql=sql)
                self.logging.info('mysql | 数据库任务已删除: {}'.format(sha))
            except:
                self.logging.warning('mysql | 数据库任务删除异常: {}'.format(sha))

        elif url:
            try:
                sql = "delete from {} where `url` = '{}' and `del` = '0'".format(table, url)
                self.mysql_client.get_result(sql=sql)
                self.logging.info('mysql | 数据库任务已删除: {}'.format(url))
            except:
                self.logging.warning('mysql | 数据库任务删除异常: {}'.format(url))

    def delete_logic_task_from_mysql(self, table, sha=None, url=None):
        self.timer.start()
        self._delete_logic_task_from_mysql(table, sha, url)
        self.logging.info('mysql end | 数据库逻辑删除任务 | use time: {}'.format(self.timer.use_time()))

    # 逻辑删除mysql中任务
    def _delete_logic_task_from_mysql(self, table, sha=None, url=None):
        data = {
            'del': '1'
        }
        if sha:
            try:
                self.mysql_client.update(table=table, data=data, where="`sha` = '{}' and `del` = '0'".format(sha))
                self.logging.info('mysql | 数据库任务已逻辑删除: {}'.format(sha))
            except:
                self.logging.warning('mysql | 数据库任务逻辑删除异常: {}'.format(sha))

        elif url:
            try:
                self.mysql_client.update(table=table, data=data, where="url = '{}' and `del` = '0'".format(url))
                self.logging.info('mysql | 数据库任务已逻辑删除: {}'.format(url))
            except:
                self.logging.warning('mysql | 数据库任务逻辑删除异常: {}'.format(url))

    def finish_task_from_mysql(self, table, sha=None, url=None):
        self.timer.start()
        self._finish_task_from_mysql(table, sha, url)
        self.logging.info('mysql end | 数据库任务已完成 | use time: {}'.format(self.timer.use_time()))

    # mysql中已完成任务
    def _finish_task_from_mysql(self, table, sha=None, url=None):
        data = {
            'del': '2'
        }
        if sha:
            try:
                self.mysql_client.update(table=table, data=data, where="`sha` = '{}' and `del` = '0'".format(sha))
                self.logging.info('mysql | 数据库任务已完成: {}'.format(sha))
            except:
                self.logging.warning('mysql | 数据库已完成任务标记异常: {}'.format(sha))

        elif url:
            try:
                self.mysql_client.update(table=table, data=data, where="url = '{}' and `del` = '0'".format(url))
                self.logging.info('mysql | 数据库任务已完成: {}'.format(url))
            except:
                self.logging.warning('mysql | 数据库已完成任务标记异常: {}'.format(url))


if __name__ == '__main__':
    pass
