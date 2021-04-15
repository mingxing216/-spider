#-*-coding:utf-8-*-

from ProxyPool.Common.db import RedisClient
from ProxyPool.ProxyGetter.crawler import Crawler
from ProxyPool.setting import *
import sys

class Getter():
    def __init__(self):
        self.redis = RedisClient()
        self.crawler = Crawler()
    
    def is_over_threshold(self):
        """
        判断是否达到了代理池限制
        """
        if self.redis.count() >= POOL_UPPER_THRESHOLD:
            return True
        else:
            return False
    
    def run(self):
        print('获取器开始执行')
        if not self.is_over_threshold():
            for callback_label in range(self.crawler.__CrawlFuncCount__):
                callback = self.crawler.__CrawlFunc__[callback_label]
                # 获取代理
                proxies = self.crawler.get_proxies(callback, PROXIES_NUM)
                sys.stdout.flush()
                for proxy in proxies:
                    val = self.redis.score(proxy)
                    print('返回值: {}'.format(val))
                    if val is not None:
                        continue
                    self.redis.add(proxy)
                    print('添加到代理池中')

            count = self.redis.count()
            print('当前代理池有', count, '个代理')
            if count > POOL_MAX_COUNT:
                del_clunt = self.redis.delete()

                if del_clunt:
                    print('已删除 {}-{} 区间的代理'.format(DELETE_MIN, DELETE_MAX))
                else:
                    print('代理池中已无 {}-{} 区间代理'.format(DELETE_MIN, DELETE_MAX))


if __name__ == '__main__':
    getter = Getter()
    getter.run()
