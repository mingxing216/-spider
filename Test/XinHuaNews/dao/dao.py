# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import mysqlpool_utils
from Utils import proxy_utils
from Downloader import downloader


class Dao(object):
    def __init__(self, logging):
        self.logging = logging
        self.ss_xinhua_news_url = 'ss_xinhua_news_url' # mysql记录已抓新闻的表名

    # 查询当前新闻是否被抓取过 True(抓过)、False(未抓过)
    def new_status(self, mysql_client, new_url):
        # 生成sha1加密
        sha = hashlib.sha1(new_url.encode('utf-8')).hexdigest()

        sql = 'select sha from {} where sha = "{}"'.format(self.ss_xinhua_news_url, sha)
        # 查询
        data = mysqlpool_utils.get_results(connection=mysql_client, sql=sql)
        if data:
            return True
        else:
            return False

    # 保存图片到hbase
    def saveImg(self, media_url, content, type, item):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        data = {"ip": "{}".format(proxy_utils.getLocalIP()),
                "wid": "100",
                "url": "{}".format(media_url),
                "content": "{}".format(content.decode('utf-8')),
                "type": "{}".format(type),
                "ref": "",
                "item": json.dumps(item)}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        download = downloader.Downloads(logging=self.logging, headers=headers)
        resp = download.newGetRespForPost(url=url, data=data)
        return resp

    # 存储专利数据到Hbase数据库
    def saveData(self, data):
        save_data = json.dumps(data)
        url = '{}'.format(settings.SpiderDataSaveUrl)
        data = {"ip": "{}".format(proxy_utils.getLocalIP()),
                "wid": "python",
                "ref": "",
                "item": save_data}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }
        download = downloader.Downloads(logging=self.logging, headers=headers)
        resp = download.newGetRespForPost(url=url, data=data)
        return resp

    def demo(self, **kwargs):
        '''
        demo函数， 仅供参考
        '''
        mysql_client = kwargs['mysql_client']
        sha = kwargs['sha']
        sql = "select sha from ss_paper where `sha` = '%s'" % sha
        status = mysqlpool_utils.get_results(connection=mysql_client, sql=sql)
        if status:

            return False
        else:

            return True
