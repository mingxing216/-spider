# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import mysqlpool_utils
from Utils import redispool_utils
from Utils import proxy_utils
from Downloader import downloader


# [redis]万方专利redis任务队列名
WANFANG_PATENT_URL_Q = 'wanfang_patent_url_q'
# [mysql]存储万方专利url的表名
WANFANG_PATENT_URL = 'ss_patent_wanfang'


# 存储专利url到mysql数据库
def savePatentUrlInMysql(logging, connection, url, country_name):
    data = {
            'url': url,
            'country': country_name
            }
    mysqlpool_utils.insert_one(connection=connection, table=WANFANG_PATENT_URL, data=data)

# 查询redis中万方专利队列任务数
def getRedisPatentUrlNumber(redis_client):
    number = redispool_utils.scard(redis_client=redis_client, key=WANFANG_PATENT_URL_Q)

    return number

# 从mysql中获取1000个专利任务
def getPatentUrl_1000(connection):
    sql = "select url, country from {} where `del` is NULL limit 1000".format(WANFANG_PATENT_URL)
    datas = mysqlpool_utils.get_results(connection=connection, sql=sql)

    return datas

# 将万方专利任务队列至redis
def input_patent_url_to_redis(redis_client, url):
    redispool_utils.sadd(redis_client=redis_client, key=WANFANG_PATENT_URL_Q, value=url)

# 从redis中获取100个任务
def getPatentUrlForRedis(redis_client):
    datas = redispool_utils.queue_spops(redis_client=redis_client, key=WANFANG_PATENT_URL_Q, lockname='wanfang_patent_url_lock', count=100)

    return datas

# 保存万方专利到hbase
def savePatentDataToHbase_WanFang(logging, data):
    save_data = json.dumps(data)
    url = '{}'.format(settings.SpiderDataSaveUrl)
    data = {"ip": "{}".format(proxy_utils.getLocalIP()),
            "wid": "python",
            "ref": "",
            "item": save_data}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }

    resp = downloader.newGetRespForPost(logging=logging, url=url, data=data, headers=headers)
    return resp

# 修改mysql专利状态
def updatePatentDataToMysql(mysql_client, patent_url, country):
    data = {
        'url': patent_url,
        'del': 1,
        'country': country
    }
    mysqlpool_utils.update(connection=mysql_client, table=WANFANG_PATENT_URL, data=data, where="url = '{}'".format(patent_url))