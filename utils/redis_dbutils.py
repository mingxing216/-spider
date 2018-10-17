# -*- coding: utf-8 -*-

'''
本文件提供redis数据库操作公共方法
'''
import sys, os
from redis import StrictRedis

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from utils import timeutils


def create_redis():
    '''
    创建redis对象
    :return: redis对象
    '''
    redis_host = settings.REDIS_HOST
    redis_port = settings.REDIS_PORT
    redis_password = settings.REDIS_PASSWORD
    redis_server = StrictRedis(host=redis_host, port=redis_port, password=redis_password)

    return redis_server


def redisLock(func):
    # 锁的过期时间（秒）
    EXPIRY = 3

    def wrapper(*args, **kwargs):
        if kwargs['lockname']:
            lockname = kwargs['lockname']
        else:
            lockname = 'lock.foo'
        redis_client = create_redis()
        while True:
            # 获取当前时间戳
            now = timeutils.get_current_millis()
            # 生成锁时间【当前时间戳 + 锁有效时间】
            lock_time_out = now + EXPIRY
            # 设置redis锁
            lock_status = redis_client.setnx(lockname, lock_time_out)
            # 如果返回1， 代表抢锁成功
            if lock_status == 1:
                data = func(*args, **kwargs)
                # 获取当前时间戳
                now = timeutils.get_current_millis()
                # 获取当前redis设置的锁时间戳
                now_redis_lock = redis_client.get(lockname)
                # 如果当前时间戳小于锁设置时间， 解锁
                if int(now) < int(now_redis_lock):
                    redis_client.delete(lockname)

                return data
            # 如果返回0， 代表抢锁失败
            if lock_status == 0:
                # 获取redis中锁的过期时间
                redis_lock_out = redis_client.get(lockname)
                # 判断这个锁是否已超时, 如果当前时间大于锁时间， 说明锁已超时
                if now > int(redis_lock_out):
                    # 生成锁时间【当前时间戳 + 锁有效时间】
                    lock_time_out = now + EXPIRY
                    # 抢锁
                    old_lock_time = redis_client.getset(lockname, lock_time_out)
                    # 判断抢锁后返回的时间是否与之前获取的锁过期时间相等， 相等说明抢锁成功
                    if int(old_lock_time) == int(redis_lock_out):
                        data = func(*args, **kwargs)
                        # 获取当前时间戳
                        now = timeutils.get_current_millis()
                        # 获取当前redis设置的锁时间戳
                        now_redis_lock = redis_client.get(lockname)
                        # 如果当前时间戳小于锁设置时间， 解锁
                        if int(now) < int(now_redis_lock):
                            redis_client.delete(lockname)

                        return data
                    else:
                        # 抢锁失败， 重新再抢
                        continue

    return wrapper

# 获取并删除一个set元素【分布式】
@redisLock
def queue_spop(**kwargs):
    '''
    获取并删除集合中的一个元素
    :param kwargs: 
    :return: 被删除的元素
    使用案例 data = spop(key='comlieted', lockname='spop_demo')
    注意： 必须设置lockname， 本函数基于分布式， lockname是用来设置redis锁的。不设置会出问题， 名字根据自己喜好起
    '''
    redis_server = create_redis()
    return redis_server.spop(kwargs['key'])


def getList(key, start, end):
    '''
    获取列表类型内容
    :param key: 列表名
    :param start: 开始索引
    :param end: 结束索引
    :return: 查询出的列表
    '''
    redis_server = create_redis()
    data = redis_server.lrange(key, start, end)

    return data

def saveList(key, value):
    '''
    保存单个数据到列表类型
    :param key: 列表名
    :param value: 值
    '''
    redis_server = create_redis()
    len_list = redis_server.lpush(key, value)

    return len_list # 列表中的元素数量

def getSetNumber(key):
    '''
    获取redis集合内元素数量
    :param key: 集合名
    :return: 元素数量
    '''
    redis_server = create_redis()
    proxy_number = redis_server.scard(key)

    return proxy_number

def saveSet(key, value):
    '''
    保存单个数据到集合
    :param key: 集合名
    :param value: 元素
    :return: 元素数量
    '''
    redis_server = create_redis()
    ok_number = redis_server.sadd(key, value)

    return ok_number  # 插入成功数量

def srandmember(key, num):
    '''
    从集合中随机获取num个元素
    :param key: 集合名
    :param num: 获取数量
    :return: 元素列表
    '''
    redis_server = create_redis()
    data = redis_server.srandmember(key, num)
    data_list = []
    for proxy_b in data:
        proxy = proxy_b.decode('utf8')
        data_list.append(proxy)

    return data_list

def srem(key, value):
    '''
    删除redis集合内的value元素
    :param key: 集合名
    :param value: 元素
    '''
    redis_server = create_redis()
    redis_server.srem(key, value)

def sismember(key, value):
    '''
    判断数据是都存在集合中
    :param key:
    :param value:
    :return:
    '''
    redis_server = create_redis()

    return redis_server.sismember(key, value)

def smembers(key):
    '''
    查询集合内所有元素
    :param key: 键
    :return: 值
    '''
    redis_server = create_redis()

    return redis_server.smembers(key)


