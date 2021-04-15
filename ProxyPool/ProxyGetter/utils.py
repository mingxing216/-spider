#-*-coding:utf-8-*-

import requests
import time
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout


def get_page(url):
    """
    抓取代理
    :param url:
    :param options:
    :return:
    """
    print('正在抓取', url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        # 'Accept-Encoding': 'gzip, deflate, sdch',
        # 'Accept-Language': 'zh-CN,zh;q=0.8'
    }

    # 重试次数
    for i in range(5):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print('抓取成功', url, response.status_code)
            if response.status_code == 200:
                return response.text
        except (ConnectionError, ConnectTimeout, ReadTimeout):
            print('再试一次', url)
            time.sleep(2)
            continue

    else:
        print('抓取失败', url)
        return None
