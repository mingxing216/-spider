# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
import json
import base64

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import mysqlpool_utils
from Utils import proxy_utils
from Downloader import downloader


SS_XINHUA_NEWS_URL = 'ss_xinhua_news_url' # mysql记录已抓新闻的表名

# 查询当前新闻是否被抓取过 True(抓过)、False(未抓过)
def new_status(mysql_client, new_url):
    # 生成sha1加密
    sha = hashlib.sha1(new_url.encode('utf-8')).hexdigest()

    sql = 'select sha from {} where sha = "{}"'.format(SS_XINHUA_NEWS_URL, sha)
    # 查询
    data = mysqlpool_utils.get_results(connection=mysql_client, sql=sql)
    if data:
        return True
    else:
        return False

# 保存图片到hbase
def saveImg(logging, media_url, content, type):
    url = '{}'.format(settings.SpiderMediaSaveUrl)
    content_bs64 = base64.b64encode(content)
    sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
    item = {
        'pk': sha,
        'type': 'image',
        'url': media_url
    }
    data = {"ip": "{}".format(proxy_utils.getLocalIP()),
            "wid": "100",
            "url": "{}".format(media_url),
            "content": "{}".format(content_bs64.decode('utf-8')),
            "type": "{}".format(type),
            "ref": "",
            "item": json.dumps(item)}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }

    resp = downloader.newGetRespForPost(logging=logging, url=url, headers=headers, data=data)

    return resp

# 存储专利数据到Hbase数据库
def saveData(data, logging):
    save_data = json.dumps(data)
    url = '{}'.format(settings.SpiderDataSaveUrl)
    data = {"ip": "{}".format(proxy_utils.getLocalIP()),
            "wid": "python",
            "ref": "",
            "item": save_data}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    resp = downloader.newGetRespForPost(logging=logging, url=url, headers=headers, data=data)

    return resp

