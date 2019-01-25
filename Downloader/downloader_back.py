# -*-coding:utf-8-*-

'''
下载器
'''

import sys
import os
import requests
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")


def newGetRespForGet(logging, url, headers, proxies=None, cookies=None):
    '''
    get请求下载器
    :param logging: log对象
    :param url: url
    :param headers: 请求头
    :param proxies: 代理IP
    :return: 响应结果
    '''
    try:
        resp = requests.get(url=url, headers=headers, proxies=proxies, timeout=10, cookies=cookies)
        if resp.status_code == 200:
            response = resp.content.decode('utf-8')
            resp.close()
            return response

        else:
            logging.error('HTTP异常返回码： {}'.format(resp.status_code))
            # time.sleep(1)

            return None

    except ConnectTimeout or ReadTimeout:
        logging.error('Connect Timeout')
        # time.sleep(0.2)

        return None

    except ConnectionError as e:
        logging.error(e)
        # time.sleep(0.2)

        return None

    except Exception as e:
        logging.error(e)
        # time.sleep(0.2)

        return None


def newGetRespForPost(logging, url, headers, data, proxies=None, cookies=None):
    '''
    post请求下载器
    :param logging: log对象
    :param url: url
    :param headers: 请求头
    :param data: 请求参数
    :param proxies: 代理IP
    :param cookies: 登录cookie
    :return: 响应结果
    '''
    try:
        resp = requests.post(url=url, data=data, headers=headers, proxies=proxies, timeout=10, cookies=cookies)
        if resp.status_code == 200:
            response = resp.content.decode('utf-8')
            resp.close()
            return response

        else:
            logging.error('HTTP异常返回码： {}'.format(resp.status_code))
            # time.sleep(1)

            return None

    except ConnectTimeout or ReadTimeout:
        logging.error('Connect Timeout')
        # time.sleep(0.2)

        return None

    except ConnectionError as e:
        logging.error(e)
        # time.sleep(0.2)

        return None

    except Exception as e:
        logging.error(e)
        # time.sleep(0.2)

        return None


# 下载流媒体
def downMedia(logging, url, headers, proxies=None):
    '''
    流媒体下载器
    :param logging: log对象
    :param url: url
    :param headers: 请求头
    :param proxies: 代理IP
    :return: 流媒体内容
    '''
    try:
        resp = requests.get(url=url, headers=headers, proxies=proxies)
        if resp.status_code == 200:
            response = resp.content
            resp.close()
            return response

        else:
            logging.error('HTTP异常返回码： {}, 异常url: {}'.format(resp.status_code, url))
            # time.sleep(1)

            return None

    except ConnectTimeout or ReadTimeout:
        logging.error('Connect Timeout')
        # time.sleep(0.2)

        return None

    except ConnectionError as e:
        logging.error(e)
        # time.sleep(0.2)

        return None

    except Exception as e:
        logging.error(e)
        # time.sleep(0.2)

        return None
