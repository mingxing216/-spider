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
from Utils import redispool_utils
from Utils import proxy_utils
from Log import log

log_file_dir = 'proxy_set_mail_pool_http_main'  # LOG日志存放路径
LOGNAME = '<按套餐提取代理>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

# redis对象
redis_client = redispool_utils.createRedisPool()


def maintainProxyPool():
    '''
    代理池维护
    '''
    redis_key = settings.REDIS_PROXY_KEY_HTTP
    redis_proxy_number = settings.REDIS_PROXY_NUMBER_HTTP
    server = proxy_pool_service.ProxySetMealServices()
    while True:
        proxy_number = server.getProxyPoolLen(redis_client=redis_client, key=redis_key)

        if proxy_number < int(redis_proxy_number):
            get_proxy_num = int(redis_proxy_number) - proxy_number
            proxys = server.getZhiMaProxy(num=get_proxy_num, protocol=1)
            if proxys is not None:
                for proxy_dict in proxys:
                    proxy = 'http://%s:%s' % (proxy_dict['ip'], proxy_dict['port'])
                    # # 检测代理是否高匿
                    # proxy_stutus = proxy_utils.jianChaNiMingDu(proxy=proxy, logging=LOGGING)
                    # if proxy_stutus:
                    #     redispool_utils.sadd(redis_client=redis_client, key=redis_key, value=proxy)
                    #     LOGGING.info('Save proxy in redis: {}'.format(proxy))
                    redispool_utils.sadd(redis_client=redis_client, key=redis_key, value=proxy)
                    LOGGING.info('Save proxy in redis: {}'.format(proxy))
            else:
                LOGGING.error('Get proxy failed!!!')

        time.sleep(1)


if __name__ == '__main__':

    maintainProxyPool()
