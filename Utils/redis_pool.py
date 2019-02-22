# -*-coding:utf-8-*-
'''
redis连接池操作
'''

import redis
import sys
import os
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from Utils import timeutils


# 分布式锁
def _redisLock(func):
    # 锁的过期时间（秒）
    EXPIRY = 3

    def wrapper(self, *args, **kwargs):
        if kwargs['lockname']:
            lockname = kwargs['lockname']
        else:
            lockname = 'lock.foo'

        while True:
            # 获取当前时间戳
            now = timeutils.get_current_second()
            # 生成锁时间【当前时间戳 + 锁有效时间】
            lock_time_out = now + EXPIRY
            # 设置redis锁
            lock_status = self.redis_client.setnx(lockname, lock_time_out)
            # 如果返回1， 代表抢锁成功
            if lock_status == 1:
                data = func(self, *args, **kwargs)
                # 获取当前时间戳
                now = timeutils.get_current_second()
                # 获取当前redis设置的锁时间戳
                now_redis_lock = self.redis_client.get(lockname)
                if now_redis_lock:
                    # 如果当前时间戳小于锁设置时间， 解锁
                    if int(now) < int(now_redis_lock):
                        self.redis_client.delete(lockname)

                    return data
            # 如果返回0， 代表抢锁失败
            if lock_status == 0:
                # 获取redis中锁的过期时间
                redis_lock_out = self.redis_client.get(lockname)
                # 判断这个锁是否已超时, 如果当前时间大于锁时间， 说明锁已超时
                if redis_lock_out:
                    if now > int(redis_lock_out):
                        # 生成锁时间【当前时间戳 + 锁有效时间】
                        lock_time_out = now + EXPIRY
                        # 抢锁
                        old_lock_time = self.redis_client.getset(lockname, lock_time_out)
                        # 判断抢锁后返回的时间是否与之前获取的锁过期时间相等， 相等说明抢锁成功
                        if int(old_lock_time) == int(redis_lock_out):
                            data = func(self, *args, **kwargs)
                            # 获取当前时间戳
                            now = timeutils.get_current_second()
                            # 获取当前redis设置的锁时间戳
                            now_redis_lock = self.redis_client.get(lockname)
                            # 如果当前时间戳小于锁设置时间， 解锁
                            if int(now) < int(now_redis_lock):
                                self.redis_client.delete(lockname)

                            return data
                        else:
                            # 抢锁失败， 重新再抢
                            continue

    return wrapper


class RedisPoolUtils(object):
    def __init__(self, number=settings.REDIS_POOL_MAX_NUMBER):
        self.REDIS_HOST = settings.REDIS_HOST
        self.REDIS_PORT = settings.REDIS_PORT
        self.REDIS_PASSWORD = settings.REDIS_PASSWORD
        self.REDIS_POOL_MAX_NUMBER = number
        def createRedisPool():
            '''
            创建redis连接池
            :return: redis对象
            '''
            pool = redis.ConnectionPool(host=self.REDIS_HOST, port=self.REDIS_PORT, password=self.REDIS_PASSWORD,
                                        max_connections=self.REDIS_POOL_MAX_NUMBER)
            redis_client = redis.StrictRedis(connection_pool=pool)
            return redis_client

        self.redis_client = createRedisPool()

    # 获取并删除一个set元素【分布式】
    @_redisLock
    def queue_spop(self, **kwargs):
        '''
        :param key: 键
        注意： 必须设置lockname， 本函数基于分布式， lockname是用来设置redis锁的。不设置会出问题， 名字根据自己喜好起
        :return:元素
        '''
        data = self.redis_client.spop(kwargs['key'])
        if data:
            data = data.decode('utf-8')
            return data

        return None

    # 获取并删除多个set元素【分布式】
    @_redisLock
    def queue_spops(self, **kwargs):
        '''
        :param key: 键
        :param count: 获取数量
        :return: 元素列表
        '''
        return_data = []
        try:
            count = kwargs['count']
        except:
            count = 1
        for i in range(count):
            data = self.redis_client.spop(kwargs['key'])
            if data:
                data = data.decode('utf-8')
                return_data.append(data)
            else:
                continue

        return return_data

    # 设置值
    def setValue(self, key, value, over_time=None):
        '''
        :param key: 键
        :param value: 值
        :return: True/False
        '''
        status = self.redis_client.set(key, value)

        if over_time:
            self.redis_client.expire(key, over_time)

        return status

    # 获取值
    def getValue(self, key):
        '''
        :param key: 键
        :return: 值
        '''
        data = self.redis_client.get(key)

        return data.decode('utf-8')

    # 设置key过期时间
    def setUpOvertime(self, key, over_time):
        '''
        :param key: 键
        :param over_time: 有效期【秒】
        :return: Ture/False
        '''
        status = self.redis_client.expire(key, over_time)

        return status

    # 删除key
    def delete(self, key):
        '''
        :param key: 键
        :return: 成功数|失败0
        '''
        status = self.redis_client.delete(key)

        return status

    # 获取列表类型内容
    def lrange(self, key, start, end):
        '''
        :param key: 列表名
        :param start: 开始索引
        :param end: 结束索引
        :return: 查询出的列表
        '''
        return_data = []
        datas = self.redis_client.lrange(key, start, end)
        for data in datas:
            data = data.decode('utf-8')
            return_data.append(data)
        return return_data

    # 保存数据到列表类型
    def lpush(self, key, value):
        '''
        :param key: 列表名
        :param value: 值
        '''
        len_list = self.redis_client.lpush(key, value)

        return len_list  # 列表中的元素数量

    # 删除列表类型元素
    def lrem(self, key, count, value):
        '''
        :param key: key
        :param count: 删除个数
        :param value: value
        :return: 删除成功数
        '''
        status = self.redis_client.lrem(name=key, count=count, value=value)

        return status

    # 获取集合类型内元素数量】
    def scard(self, key):
        '''
        :param key: 集合名
        :return: 元素数量
        '''
        proxy_number = self.redis_client.scard(key)

        return proxy_number

    # 保存单个元素到集合
    def sadd(self, key, value):
        '''
        :param key: 集合名
        :param value: 元素
        :return: 当前元素数量
        '''
        ok_number = self.redis_client.sadd(key, value)

        return ok_number  # 插入成功数量

    # 从集合中随机获取num个元素
    def srandmember(self, key, num):
        '''
        :param key: 集合名
        :param num: 获取数量
        :return: 元素列表
        '''
        data = self.redis_client.srandmember(key, num)
        data_list = []
        for proxy_b in data:
            proxy = proxy_b.decode('utf8')
            data_list.append(proxy)

        return data_list

    # 删除集合内元素
    def srem(self, key, value):
        '''
        :param key: 集合名
        :param value: 元素
        :return: 成功数
        '''
        status = self.redis_client.srem(key, value)

        return status

    # 判断元素是否在集合内
    def sismember(self, key, value):
        '''
        :param key:
        :param value:
        :return: True | False
        '''

        return self.redis_client.sismember(key, value)

    # 查询集合内所有元素
    def smembers(self, key):
        '''
        查询集合内所有元素
        :param key: 键
        :return: 值
        '''
        return_data = []
        datas = self.redis_client.smembers(key)
        for data in datas:
            data = data.decode('utf-8')
            return_data.append(data)

        return return_data


if __name__ == '__main__':
    obj = RedisPoolUtils()
    data = obj.smembers(key='demo')
    print(data)




