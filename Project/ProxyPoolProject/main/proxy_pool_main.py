# -*-coding:utf-8-*-

'''
按次提取代理IP
'''

import os
import sys
import time
from multiprocessing import Process

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from log import log
from Project.ProxyPoolProject.services import proxy_pool_service
from utils import redispool_utils

logname = 'proxy_pool_main'
logging = log.ILog(logname)

# redis对象
redis_client = redispool_utils.createRedisPool()


def maintainProxyPool():
    '''
    代理池维护
    '''

    # 必要参数
    redis_key = settings.REDIS_PROXY_KEY
    redis_proxy_number = settings.REDIS_PROXY_NUMBER

    # 模块对象
    service = proxy_pool_service.ProxyServices()

    # 主体逻辑
    proxy_number = service.getProxyPoolLen(redis_client=redis_client, key=redis_key)
    if proxy_number < int(redis_proxy_number):
        get_proxy_num = int(redis_proxy_number) - proxy_number
        proxys = service.getZhiMaProxy(get_proxy_num)
        if proxys is not None:
            for proxy_dict in proxys:
                proxy = 'socks5://%s:%s' % (proxy_dict['ip'], proxy_dict['port'])
                redispool_utils.sadd(redis_client=redis_client, key=redis_key, value=proxy)
                logging.info('Save proxy in redis: {}'.format(proxy))
        else:
            logging.error('Get proxy failed!!!')


if __name__ == '__main__':
    while True:
        # p1 = Process(target=accountBalance)
        p2 = Process(target=maintainProxyPool)
        # p1.start()
        p2.start()
        # p1.join()
        p2.join()

        time.sleep(2)
