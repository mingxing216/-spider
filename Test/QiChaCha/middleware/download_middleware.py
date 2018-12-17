# -*-coding:utf-8-*-

'''

'''
import sys
import os
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agents
from Utils import proxy_utils

class Download_Middleware():
    def __init__(self, logging):
        self.logging = logging


    def demo(self, **kwargs):
        '''
        获取响应【demo函数, 仅供参考】
        :param kwargs: 主要接收参数： redis_client, url, logging
        :return: 响应内容
        '''
        url = kwargs['url']
        headers = {
            'User-Agent': random.sample(user_agents.ua_for_win, 1)[0]
        }
        downloading = downloader.Downloads(headers=headers, logging=self.logging)
        resp = downloading.newGetRespForGet(url=url)

        return resp





