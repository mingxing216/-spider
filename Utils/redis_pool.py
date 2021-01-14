# -*- coding:utf-8 -*-

"""
redis连接池操作
"""

import redis

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
                lock_data = func(self, *args, **kwargs)
                # 获取当前时间戳
                now = timeutils.get_current_second()
                # 获取当前redis设置的锁时间戳
                now_redis_lock = self.redis_client.get(lockname)
                if now_redis_lock:
                    # 如果当前时间戳小于锁设置时间， 解锁
                    if int(now) < int(now_redis_lock):
                        self.redis_client.delete(lockname)

                    return lock_data
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
                            lock_data = func(self, *args, **kwargs)
                            # 获取当前时间戳
                            now = timeutils.get_current_second()
                            # 获取当前redis设置的锁时间戳
                            now_redis_lock = self.redis_client.get(lockname)
                            # 如果当前时间戳小于锁设置时间， 解锁
                            if int(now) < int(now_redis_lock):
                                self.redis_client.delete(lockname)

                            return lock_data
                        else:
                            # 抢锁失败， 重新再抢
                            continue

    return wrapper


class RedisPoolUtils(object):
    def __init__(self, number):
        self.redis_host = settings.REDIS_HOST
        self.redis_port = settings.REDIS_PORT
        self.redis_password = settings.REDIS_PASSWORD
        self.redis_pool_max_number = number
        self.pool = redis.ConnectionPool(host=self.redis_host, port=self.redis_port, password=self.redis_password,
                                         max_connections=self.redis_pool_max_number)

    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self.get_connection()

        return self._conn

    def get_connection(self):
        self._conn = redis.StrictRedis(connection_pool=self.pool)

    # 获取并删除一个set元素【分布式】
    # @_redisLock
    def queue_spop(self, **kwargs):
        """
        :param key: 键
        注意： 必须设置lockname， 本函数基于分布式， lockname是用来设置redis锁的。不设置会出问题， 名字根据自己喜好起
        :return:元素
        """
        value = self.conn.spop(kwargs['key'])
        if value:
            value = value.decode('utf-8')
            return value

        return None

    # 获取并删除多个set元素【分布式】
    # @_redisLock
    def queue_spops(self, **kwargs):
        """
        :param key: 键
        :param count: 获取数量
        :return: 元素列表
        """
        return_data = []
        try:
            count = kwargs['count']
        except:
            count = 1
        for i in range(count):
            re_value = self.conn.spop(kwargs['key'])
            if re_value:
                re_value = re_value.decode('utf-8')
                return_data.append(re_value)
            else:
                continue

        return return_data

    # 设置值
    def setValue(self, key, value, over_time=None):
        """
        :param key: 键
        :param value: 值
        :return: True/False
        """
        status = self.conn.set(key, value)

        if over_time:
            self.conn.expire(key, over_time)

        return status

    # 获取值
    def getValue(self, key):
        """
        :param key: 键
        :return: 值
        """
        re_value = self.conn.get(key)

        return re_value.decode('utf-8')

    # 设置key过期时间
    def setUpOvertime(self, key, over_time):
        """
        :param key: 键
        :param over_time: 有效期【秒】
        :return: Ture/False
        """
        status = self.conn.expire(key, over_time)

        return status

    # 删除key
    def delete(self, key):
        """
        :param key: 键
        :return: 成功数|失败0
        """
        status = self.conn.delete(key)

        return status

    # 获取列表类型内容
    def lrange(self, key, start, end):
        """
        :param key: 列表名
        :param start: 开始索引
        :param end: 结束索引
        :return: 查询出的列表
        """
        return_data = []
        datas = self.conn.lrange(key, start, end)
        for re_value in datas:
            re_value = re_value.decode('utf-8')
            return_data.append(re_value)
        return return_data

    # 保存数据到列表类型
    def lpush(self, key, value):
        """
        :param key: 列表名
        :param value: 值
        """
        len_list = self.conn.lpush(key, value)

        return len_list  # 列表中的元素数量

    # 删除列表类型元素
    def lrem(self, key, count, value):
        """
        :param key: key
        :param count: 删除个数
        :param value: value
        :return: 删除成功数
        """
        status = self.conn.lrem(name=key, count=count, value=value)

        return status

    # 获取集合类型内元素数量
    def scard(self, key):
        """
        :param key: 集合名
        :return: 元素数量
        """
        proxy_number = self.conn.scard(key)

        return proxy_number

    # 保存单个元素到集合
    def sadd(self, key, value):
        """
        :param key: 集合名
        :param value: 元素
        :return: 当前元素数量
        """
        ok_number = self.conn.sadd(key, value)

        return ok_number  # 插入成功数量

    # 从集合中随机获取num个元素
    def srandmember(self, key, num):
        """
        :param key: 集合名
        :param num: 获取数量
        :return: 元素列表
        """
        re_value = self.conn.srandmember(key, num)
        data_list = []
        for proxy_b in re_value:
            proxy = proxy_b.decode('utf8')
            data_list.append(proxy)

        return data_list

    # 删除集合内元素
    def srem(self, key, value):
        """
        :param key: 集合名
        :param value: 元素
        :return: 成功数
        """
        status = self.conn.srem(key, value)

        return status

    # 判断元素是否在集合内
    def sismember(self, key, value):
        """
        :param key:
        :param value:
        :return: True | False
        """

        return self.conn.sismember(key, value)

    # 查询集合内所有元素
    def smembers(self, key):
        """
        查询集合内所有元素
        :param key: 键
        :return: 值
        """
        return_data = []
        datas = self.conn.smembers(key)
        for re_value in datas:
            re_value = re_value.decode('utf-8')
            return_data.append(re_value)

        return return_data


if __name__ == '__main__':
    obj = RedisPoolUtils(5)
    record = obj.sadd('demo', '2021年了')
    data = obj.smembers('demo')
    print(data)
