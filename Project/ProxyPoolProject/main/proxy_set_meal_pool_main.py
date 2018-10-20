# -*-coding:utf-8-*-

'''
套餐提取代理IP
'''
import os
import sys
import time
from multiprocessing import Process
sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Project.ProxyPoolProject.services import proxy_pool_service
from Project.ProxyPoolProject.spiders import proxy_pool_spider
from utils import redis_dbutils
from log import log

logname = 'proxy_pool_main'
logging = log.ILog(logname)


def setMealProxyNumber():
    '''
    当前套餐可用代理数量
    '''
    server = proxy_pool_service.ProxySetMealServices()
    proxy_number = server.setMealProxyNumber()
    if proxy_number < 10:
        logging.error('In the set meal, the number of agents is less than 10')
    else:
        logging.info('Set meal have proxy: {}'.format(proxy_number))


def maintainProxyPool():
    '''
    代理池维护
    '''
    redis_key = settings.REDIS_PROXY_KEY
    redis_proxy_number = settings.REDIS_PROXY_NUMBER
    server = proxy_pool_service.ProxySetMealServices()
    proxy_number = server.getProxyPoolLen(redis_key)

    if proxy_number < int(redis_proxy_number):
        get_proxy_num = int(redis_proxy_number) - proxy_number
        proxys = server.getZhiMaProxy(get_proxy_num)
        if proxys is not None:
            for proxy_dict in proxys:
                proxy = 'socks5://%s:%s' % (proxy_dict['ip'], proxy_dict['port'])
                redis_dbutils.saveSet(redis_key, proxy)
                logging.info('Save proxy in redis: {}'.format(proxy))
        else:
            logging.error('Get proxy failed!!!')


if __name__ == '__main__':
    while True:
        # p1 = Process(target=setMealProxyNumber)
        p2 = Process(target=maintainProxyPool)
        # p1.start()
        p2.start()
        # p1.join()
        p2.join()

        time.sleep(2)
