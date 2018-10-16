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
from Project.ProxyPoolProject.spiders import proxy_pool_spider
from utils import redis_dbutils

logname = 'proxy_pool_main'
logging = log.ILog(logname)


def accountBalance():
    '''
    监控账户余额
    '''

    # 必要参数
    neek = settings.NEEK
    appkey = settings.APPKEY

    # 模块对象
    service = proxy_pool_service.ProxyServices()
    spider = proxy_pool_spider

    # 主体逻辑
    api = service.createAccountBalanceApi(neek, appkey)
    balance = spider.balanceSpider(api)
    # logging.info('Account balance is {} RMB'.format(balance))


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
    proxy_number = service.getProxyPoolLen(redis_key)

    if proxy_number < int(redis_proxy_number):
        get_proxy_num = int(redis_proxy_number) - proxy_number
        proxys = service.getZhiMaProxy(get_proxy_num)
        if proxys is not None:
            for proxy_dict in proxys:
                proxy = 'socks5://%s:%s' % (proxy_dict['ip'], proxy_dict['port'])
                redis_dbutils.saveSet(redis_key, proxy)
                logging.info('Save proxy in redis: {}'.format(proxy))
        else:
            logging.error('Get proxy failed!!!')


if __name__ == '__main__':
    while True:
        p1 = Process(target=accountBalance)
        p2 = Process(target=maintainProxyPool)
        p1.start()
        p2.start()
        p1.join()
        p2.join()

        time.sleep(2)
