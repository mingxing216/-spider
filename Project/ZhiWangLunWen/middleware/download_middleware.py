# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader
from Utils import user_agent_u


class QiKanLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(QiKanLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                              timeout=timeout,
                                                              retry=retry,
                                                              update_proxy_frequency=update_proxy_frequency,
                                                              proxy_type=proxy_type,
                                                              proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if len(response) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)

    def getIndexHtml(self, url, data=None):
        param = {'url': url}
        # 设置请求方式：GET或POST
        param['mode'] = 'post'
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = {
            'productcode': 'CJFD',
            'index': 1
        }

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class HuiYiLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(HuiYiLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                              timeout=timeout,
                                                              retry=retry,
                                                              update_proxy_frequency=update_proxy_frequency,
                                                              proxy_type=proxy_type,
                                                              proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class XueWeiLunWen_QiKanTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(XueWeiLunWen_QiKanTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               retry=retry,
                                                               update_proxy_frequency=update_proxy_frequency,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class HuiYiLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(HuiYiLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               retry=retry,
                                                               update_proxy_frequency=update_proxy_frequency,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               retry=retry,
                                                               update_proxy_frequency=update_proxy_frequency,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class XueWeiLunWen_LunWenTaskDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(XueWeiLunWen_LunWenTaskDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class QiKanLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(QiKanLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               retry=retry,
                                                               update_proxy_frequency=update_proxy_frequency,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'Host': 'navi.cnki.net',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://navi.cnki.net/KNavi/Journal.html',
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class HuiYiLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(HuiYiLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                               timeout=timeout,
                                                               retry=retry,
                                                               update_proxy_frequency=update_proxy_frequency,
                                                               proxy_type=proxy_type,
                                                               proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class XueWeiLunWen_LunWenDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(XueWeiLunWen_LunWenDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class ZhiWangLunWen_JiGouDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(ZhiWangLunWen_JiGouDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class ZhiWangLunWen_ZuoZheDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(ZhiWangLunWen_ZuoZheDataDownloader, self).__init__(logging=logging,
                                                                 timeout=timeout,
                                                                 retry=retry,
                                                                 update_proxy_frequency=update_proxy_frequency,
                                                                 proxy_type=proxy_type,
                                                                 proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    # 检查验证码
    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data'].content.decode('utf-8')
                if 'window.location.href' in response:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class ZhiWangLunWen_HuiYiDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(ZhiWangLunWen_HuiYiDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data']
                if len(response.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class ZhiWangLunWen_QiKanDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(ZhiWangLunWen_QiKanDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data']
                if len(response.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class ZhiWangLunWen_WenJiDataDownloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(ZhiWangLunWen_WenJiDataDownloader, self).__init__(logging=logging,
                                                                timeout=timeout,
                                                                retry=retry,
                                                                update_proxy_frequency=update_proxy_frequency,
                                                                proxy_type=proxy_type,
                                                                proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def __judge_verify(self, param):
        while True:
            resp = self._startDownload(param=param)
            if resp['status'] != 0:
                continue

            if 'proxies' in resp:
                proxies = resp['proxies']
                response = resp['data']
                if len(response.content.decode('utf-8')) < 200:
                    self.logging.error('出现验证码')
                    # 删除代理
                    self.__del_proxies(proxies=proxies)
                    continue

                return resp

            return resp

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self.__judge_verify(param=param)


class Downloader(downloader.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, retry, update_proxy_frequency, proxy_type, proxy_country):
        super(Downloader, self).__init__(logging=logging,
                                         timeout=timeout,
                                         retry=retry,
                                         update_proxy_frequency=update_proxy_frequency,
                                         proxy_type=proxy_type,
                                         proxy_country=proxy_country)

    def __del_proxies(self, proxies):
        # 删除代理
        self.downloader.proxy_obj.delProxy(proxies=proxies)

    def getResp(self, url, mode, data=None):
        param = {'url': url}

        # 设置请求方式：GET或POST
        param['mode'] = mode
        # 设置请求头
        param['headers'] = {
            'User-Agent': user_agent_u.get_ua()
        }
        # 设置post参数
        param['data'] = data

        self.logging.info('Begin {} request for url: {} | request data is {}'.format(param['mode'], url, param['data']))
        return self._startDownload(param=param)
