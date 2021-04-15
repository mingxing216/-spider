# -*- coding:utf-8 -*-
from Utils.timers import Timer


class ProxyRule(object):
    def __init__(self, logger):
        self.logger = logger
        self.timer = Timer()

    # @staticmethod
    def get_proxy(self, conn, ws, protocol, using_time):
        """
        Get a proxy
        :param: ws: website; 多网站管理
    #   :param: protocol: http/socks5；协议，流媒体等；
    #   :param: using_time: 3/5/30s；剩余时间管理；
        :return: 随机代理
        """
        self.timer.start()
        ip = conn.random()
        if ip:
            conn.modify_score(ip, -1)
            self.logger.info('proxy | 获取代理IP成功: {} | use time: {}'.format(ip, self.timer.use_time()))
            return ip
        else:
            self.logger.error('proxy | 获取代理IP失败: {} | use time: {}'.format(ip, self.timer.use_time()))
            return ''


    # @staticmethod
    def release_proxy(self, conn, ip, result, error_score):
        """
        release proxy
        :param: ip
        :param: result: 代理成功true/代理失败false
        :return: 修改后的分数
        """
        self.timer.start()
        if result or result == 'True':
            code = conn.modify_score(ip, 1)
            if isinstance(code, (int, float)):
                self.logger.info('proxy | 释放代理IP成功: {} | use time: {}'.format(ip, self.timer.use_time()))
                return str(code)
            else:
                self.logger.error('proxy | 释放代理IP失败: {} | use time: {}'.format(ip, self.timer.use_time()))
        else:
            code = conn.modify_score(ip, error_score)
            if isinstance(code, (int, float)):
                self.logger.info('proxy | 释放代理IP成功: {} | use time: {}'.format(ip, self.timer.use_time()))
                return str(code)
            else:
                self.logger.error('proxy | 释放代理IP失败: {} | use time: {}'.format(ip, self.timer.use_time()))
