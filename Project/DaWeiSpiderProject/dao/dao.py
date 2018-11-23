# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
from pymongo.errors import DuplicateKeyError

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Utils import mysqlpool_utils
from Utils import redispool_utils
from Utils import proxy_utils
from Downloader import downloader


class Dao(object):
    def __init__(self, logging):
        self.logging = logging
        self.ss_innojoy_mobile = 'ss_innojoy_mobile' # 保存innojoy账号的mysql表名
        self.innojoy_page_number = 'innojoy_page_number' # redis中保存当前在抓页数的建
        self.innojoy_region_number = 'innojoy_region_number' # redis中保存当前专利地区分类索引的建
        self.innojoy_sic_number = 'innojoy_sic_number' # redis中保存专利分类索引的建
        self.innojoy_page_guid = 'innojoy_page_guid' # redis中保存下一页guid的建
        self.innojoy_patent_url = 'innojoy_patent_url' # redis中存储专利url的集合名
        self.innojoy_patent_url_DB = 'ss_innojoy_patent_url' # mysql中存储任务队列的表名

    # TODO 从redis获取账号池内账号
    def getPatentMobileForRedis(self, redis_client, key):
        # 查询redis账号池内有多少账号
        mobile_num = redispool_utils.scard(redis_client=redis_client, key=key)
        # 从redis账号池内获取全部账号
        mobile_list = redispool_utils.queue_spops(redis_client=redis_client, key=key, count=mobile_num, lockname=str(key) + '_lock')
        # mobile_list = redispool_utils.smembers(redis_client=redis_client, key=key)

        return mobile_list

    # 保存已注册的innojoy账号
    def saveInnojoyMobile(self, mysql_cli, data):
        save_data = {'mobile': data}
        mysqlpool_utils.insert_one(connection=mysql_cli, table=self.ss_innojoy_mobile, data=save_data)

    # 同步当前页数到redis
    def setInnojoyPage(self, redis_client, value):
        redispool_utils.redis_set(redis_client=redis_client, key=self.innojoy_page_number, value=value)

    # 同步当前专利地区分类索引到redis
    def setInnojoyRegionNumber(self, redis_client, value):
        redispool_utils.redis_set(redis_client=redis_client, key=self.innojoy_region_number, value=value)

    # 同步当前专利分类索引到redis
    def setInnojoySicNumber(self, redis_client, value):
        redispool_utils.redis_set(redis_client=redis_client, key=self.innojoy_sic_number, value=value)

    # 同步下一页guid到redis数据库
    def setInnojoyPageGuid(self, redis_client, value):
        redispool_utils.redis_set(redis_client=redis_client, key=self.innojoy_page_guid, value=value)

    # 从redis获取当前专利分类索引
    def getInnojoySicNumber(self, redis_client):
        data = redispool_utils.get(redis_client=redis_client, key=self.innojoy_sic_number)
        if data:
            return int(data)
        else:
            return 0

    # 初始化当前专利地区分类索引
    def getInnojoyRegionNumber(self, redis_client):
        data = redispool_utils.get(redis_client=redis_client, key=self.innojoy_region_number)
        if data:
            return int(data)
        else:
            return 0

    # 初始化当前在抓页数
    def getInnojoyPage(self, redis_client):
        data = redispool_utils.get(redis_client=redis_client, key=self.innojoy_page_number)
        if data:
            return int(data)
        else:
            return 1

    # 初始化下一页页码guid
    def getInnojoyPageGuid(self, redis_client):
        data = redispool_utils.get(redis_client=redis_client, key=self.innojoy_page_guid)
        if data:
            return data.decode('utf-8')
        else:
            return ''

    # 存储专利种子到mysql数据库
    def saveInnojoyPatentUrl(self, mysql_client, url):
        data = {
            'url': url
        }
        try:
            mysqlpool_utils.insert_one(connection=mysql_client, table=self.innojoy_patent_url_DB, data=data)
        except:
            pass

    # 存储专利种子到redis数据库
    def saveInnojoyPatentUrlForRedis(self, redis_client, url):
        redispool_utils.sadd(redis_client=redis_client, key=self.innojoy_patent_url, value=url)

    # 获取Innojoy专利url
    def getInnojoyPatentUrl(self, redis_client):
        patent_url = redispool_utils.queue_spop(redis_client=redis_client, key=self.innojoy_patent_url, lockname='get_innojoy_patent_url_lock')

        return patent_url

    # 保存抓取的专利数据
    def savePatentData(self, mongo_client, datas):
        try:
            mongo_client.insert_one(datas)
        except DuplicateKeyError:
            self.logging.error('已存在相同数据')
        else:
            self.logging.info('专利数据保存成功')

    # 存储专利图片到Hbase数据库
    def saveInnojoyPatentImageToHbase(self, media_url, content, type, item):
        url = '{}'.format(settings.SpiderMediaSaveUrl)
        data = {"ip": "{}".format(proxy_utils.getLocalIP()),
                "wid": "100",
                "url": "{}".format(media_url),
                "ctn": "{}".format(content),
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
    def saveInnojoyPatentDataToHbase(self, data):
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
