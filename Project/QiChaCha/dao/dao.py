# -*-coding:utf-8-*-

'''

'''
import sys
import os
import base64
import json
import hashlib

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import mysqlpool_utils
from Utils import redispool_utils
from Utils import proxy_utils
from Downloader import downloader


# 数据操作_基于登录
class Dao(object):
    def __init__(self):
        self.cookies_key = 'qiChaChaCookiePool' # 保存cookie的redis列表名
        self.company_qicha = 'ss_company_qicha' # 保存企查查任务的mysql表名
        self.objectKey = 'company_url_qicha'  # redis任务队列key

    # 获取cookie列表
    def getCookieList(self, logging, redis_client):
        cookie_list = redispool_utils.lrange(redis_client=redis_client, key=self.cookies_key, start=0, end=-1)

        return cookie_list

    # 保存企业url
    def saveCompanyUrl(self, logging, mysql_client, data):
        for company_url in data:
            # 生成sha1
            sha = hashlib.sha1(company_url.encode('utf-8')).hexdigest()

            # 查询当前数据是否已存在
            sql = "select * from {} where sha = '{}'".format(self.company_qicha, sha)
            data_status = mysqlpool_utils.execute(connection=mysql_client, sql=sql)
            if data_status:
                logging.info('企业种子已存在')
                continue
            save_data = {
                'sha': sha,
                'url': company_url
            }
            mysqlpool_utils.insert_one(connection=mysql_client, table=self.company_qicha, data=save_data)
            logging.info('企业种子保存成功')

    # 从redis获取任务
    def getObjectForRedis(self, logging, redis_client, count):
        obj_list = redispool_utils.queue_spops(redis_client=redis_client, key=self.objectKey,
                                               lockname='get_qicha_company_url_lock', count=count)

        logging.info('已获取企业任务: {}个'.format(len(obj_list)))
        return obj_list

    # 保存图片到hbase
    def saveImg(self, logging, media_url, content, type):
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
    def saveData(self, data, logging):
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


