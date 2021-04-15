# -*- coding:utf-8 -*-

import redis
from ProxyPool.Common.exception import PoolEmptyException
from ProxyPool.setting import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_KEY, REDIS_POOL_MAX_NUMBER
from ProxyPool.setting import MAX_SCORE, MIN_SCORE, INITIAL_SCORE, DELETE_MAX, DELETE_MIN
from random import choice
import re


class RedisClient(object):
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
                 max_connections=REDIS_POOL_MAX_NUMBER):
        """
        初始化
        :param host: Redis 地址
        :param port: Redis 端口
        :param password: Redis密码
        """
        # self.db = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)
        self.pool = redis.ConnectionPool(host=host, port=port, password=password,
                                         max_connections=max_connections, decode_responses=True)

    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self.get_connection()

        return self._conn

    def get_connection(self):
        self._conn = redis.Redis(connection_pool=self.pool)

    def add(self, proxy, score=INITIAL_SCORE):
        """
        添加代理，设置分数为最高
        :param proxy: 代理
        :param score: 分数
        :return: 添加结果
        """
        if not re.match('\d+\.\d+\.\d+\.\d+:\d+', proxy):
            print('代理不符合规范', proxy, '丢弃')
            return
        if not self.conn.zscore(REDIS_KEY, proxy):
            return self.conn.zadd(REDIS_KEY, {proxy: score})

    # def random(self):
    #     """
    #     随机获取有效代理，首先尝试获取最高分数代理，如果不存在，按照排名获取，否则异常
    #     :return: 随机代理
    #     """
    #     proxies = self.conn.zrangebyscore(REDIS_KEY, MAX_SCORE, MAX_SCORE)
    #     if len(proxies):
    #         return choice(proxies)
    #     else:
    #         proxies = self.conn.zrevrange(REDIS_KEY, 0, 50)
    #         if len(proxies):
    #             return choice(proxies)
    #         else:
    #             raise PoolEmptyError

    def random(self):
        """
        随机获取最高分数有效代理，如果代理池无代理，抛出异常
        :return: 随机代理
        """
        proxies = self.conn.zrangebyscore(REDIS_KEY, MAX_SCORE, MAX_SCORE)
        if len(proxies):
            return choice(proxies)
        else:
            proxies = self.conn.zrevrange(REDIS_KEY, 0, 0)
            if len(proxies):
                return proxies[0]
            else:
                raise PoolEmptyException

    def modify_score(self, proxy, num):
        """
        修改分数
        :param proxy: 代理
        :param num: 分数
        :return: 修改后的代理分数
        """
        score = self.conn.zscore(REDIS_KEY, proxy)
        if score and score > MIN_SCORE:
            return self.conn.zincrby(REDIS_KEY, int(num), proxy)
        else:
            return self.conn.zrem(REDIS_KEY, proxy)

    def remove(self, proxy):
        """
        删除代理
        :param proxy: 代理
        :return: 删除的代理
        """
        return self.conn.zrem(REDIS_KEY, proxy)

    def delete(self):
        """
        删除分数范围内代理
        :return: 删除的代理
        """
        return self.conn.zremrangebyrank(REDIS_KEY, DELETE_MIN, DELETE_MAX)

    def exists(self, proxy):
        """
        判断是否存在
        :param proxy: 代理
        :return: 是否存在
        """
        return not self.conn.zscore(REDIS_KEY, proxy) is None

    def max(self, proxy):
        """
        将代理设置为MAX_SCORE
        :param proxy: 代理
        :return: 设置结果
        """
        return self.conn.zadd(REDIS_KEY, {proxy: MAX_SCORE})

    def score(self, proxy):
        """:arg
        获取代理分数SCORE
        :param proxy: 代理
        :return: 返回结果
        """
        return self.conn.zscore(REDIS_KEY, proxy)

    def count(self):
        """
        获取数量
        :return: 数量
        """
        return self.conn.zcard(REDIS_KEY)

    def all(self):
        """
        获取全部代理
        :return: 全部代理列表
        """
        return self.conn.zrangebyscore(REDIS_KEY, MIN_SCORE, MAX_SCORE)

    def batch(self, start, stop):
        """
        批量获取
        :param start: 开始索引
        :param stop: 结束索引
        :return: 代理列表
        """
        return self.conn.zrevrange(REDIS_KEY, start, stop - 1)


if __name__ == '__main__':
    conn = RedisClient()
    result = conn.batch(0, 10)
    # print(result)
    # ip = '60.195.249.:8900'
    # print(re.match(r'\d+\.\d+\.\d+\.\d+:\d+', ip))
    print(int(-1))
    print(type(int(-1)))
    for i in range(10):
        ip = conn.random()
        conn.modify_score(ip, -1)
        print(ip)