# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agents

class Download_Middleware():
    def __init__(self):
        headers = {

            'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
        }  # 请求头

        self.downloading = downloader.Downloads(headers=headers) # 下载器对象

    def demo(self, **kwargs):
        '''
        获取响应【demo函数, 仅供参考】
        :param kwargs: 主要接收参数： redis_client, url, logging
        :return: 响应内容
        '''
        redis_client = kwargs['redis_client']
        url = kwargs['url']
        logging = kwargs['logging']
        resp = self.downloading.getRespForGet(redis_client=redis_client, url=url, logging=logging)

        if resp:
            return resp



