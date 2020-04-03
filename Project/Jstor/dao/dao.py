# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import base64
from PIL import Image
from io import BytesIO
import hashlib
import requests
import re
import time
import ast

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

import settings
from Utils import proxy
from Storage import storage
from Utils import timeutils

class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    # 种子字典存入数据库
    def saveProjectUrlToMysql(self, table, memo):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        ctx = json.dumps(memo, ensure_ascii=False)  # 参数防止中文字符串变成Unicode字节码
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'ctx': ctx,
                'url': url,
                'es': 'qikan',
                'ws': 'jstor',
                'date_created': timeutils.getNowDatetime()
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info('已存储种子: {}'.format(url))
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('种子已存在: {}'.format(sha))

    # 保存流媒体到hbase
    def saveMediaToHbase(self, media_url, content, item, type):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        # # 二进制图片文件转成base64文件
        # content_bs64 = base64.b64encode(content)

        # 截取base64图片文件
        bs = re.sub(r".*base64,", "", content, 1)
        # 解码base64图片文件
        dbs = base64.b64decode(bs)
        # 内存中打开图片
        img = Image.open(BytesIO(dbs))
        sha = hashlib.sha1(media_url.encode('utf-8')).hexdigest()
        # item = {
        #     'pk': sha,
        #     'type': type,
        #     'url': media_url,
        #     'biz_title':
        #     'length': "{}".format(len(dbs)),
        #     'natural_height': str(img['height']),
        #     'natural_width': str(img['width']),
        #     'rel_esse':
        #
        # }
        item['relEsse'] = str(item['relEsse'])
        item['relPics'] = str(item['relPics'])
        item['pk'] = sha
        item['type'] = type
        item['url'] = media_url
        item['tagSrc'] = media_url
        item['length'] = "{}".format(len(dbs))
        item['naturalHeight'] = "{}".format(img.height)
        item['naturalWidth'] = "{}".format(img.width)
        data = {"ip": "{}".format(self.proxy_obj.getLocalIP()),
                "wid": "100",
                # "content": "{}".format(content_bs64.decode('utf-8')),
                "content": "{}".format(bs),
                "ref": "",
                "item": json.dumps(item)
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        }

        start_time = time.time()
        try:
            resp = requests.post(url=url, headers=headers, data=data, timeout=10).content.decode('utf-8')
            respon = ast.literal_eval(resp)
            if respon['resultCode'] == 0:
                self.logging.info('Save media to Hbase | status: OK | sha: {} | memo: {} | use time: {}s'.format(sha, resp, '%.2f' %(time.time() - start_time)))
                return True
            else:
                self.logging.warning('Save media to Hbase | status: NO | sha: {} | memo: {} | use time: {}s'.format(sha, resp, '%.2f' %(time.time() - start_time)))
                return False
        except Exception as e:
            self.logging.error('Save media to Hbase | status: NO | sha: {} | memo: {} | use time: {}s'.format(sha, e, '%.2f' %(time.time() - start_time)))
            return False
