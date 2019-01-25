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
from Utils import timeutils
from Downloader import downloader


class Dao(object):
    def __init__(self, logging):
        self.logging = logging
        self.ss_innojoy_mobile = 'ss_innojoy_mobile' # 保存innojoy账号的mysql表名
        # self.innojoy_page_number = 'innojoy_page_number' # redis中保存当前在抓页数的建
        # self.innojoy_region_number = 'innojoy_region_number' # redis中保存当前专利地区分类索引的建
        # self.innojoy_sic_number = 'innojoy_sic_number' # redis中保存专利分类索引的建
        # self.innojoy_page_guid = 'innojoy_page_guid' # redis中保存下一页guid的建
        self.innojoy_patent_url = 'innojoy_patent_url' # redis中存储专利url的集合名
        self.innojoy_patent_url_DB = 'ss_innojoy_patent_url' # mysql中存储任务队列的表名

    # 从mysql获取innojoy账号
    def getInnojoyMobile(self, connection):
        # 获取今日时间范围
        today_start_date = timeutils.get_yyyy_mm_dd() + ' ' + '00:00:00'
        today_end_date = timeutils.get_yyyy_mm_dd() + ' ' + '23:59:59'
        # # 获取明日时间范围
        # now = timeutils.get_current_millis() + 86400
        # tomorrow_start_date = timeutils.formatMillis(timestamp=now, format='%Y-%m-%d') + ' ' + '00:00:00'
        # tomorrow_end_date = timeutils.formatMillis(timestamp=now, format='%Y-%m-%d') + ' ' + '23:59:59'
        sql = ('select * from {} where date_created not BETWEEN "{}" and "{}" and update_created not BETWEEN "{}" and "{}" limit 1;'.format(
            self.ss_innojoy_mobile, today_start_date, today_end_date, today_start_date, today_end_date))
        mobiles_list = mysqlpool_utils.get_result(connection=connection, sql=sql)

        return mobiles_list

    # 从mysql删除账号
    def deleteUser(self, connection, mobile):
        sql = 'delete from {} where `mobile` = "{}"'.format(self.ss_innojoy_mobile, mobile)
        mysqlpool_utils.execute(connection=connection, sql=sql)

    # innojoy账号存入mysql账号池
    def saveInnojoyMobile(self, mysql_cli, user):
        # 获取今日日期时间
        today_date = timeutils.get_yyyy_mm_dd_hh_mm_ss()
        # 获取明天这个时候的日期时间
        now = timeutils.get_current_millis() + 86400
        tomorrow_date = timeutils.formatMillis(timestamp=now)
        # 查询当前账号是否存在
        sql = "select mobile from {} where mobile = '{}'".format(self.ss_innojoy_mobile, user)
        user_status = mysqlpool_utils.get_results(connection=mysql_cli, sql=sql)
        if not user_status:
            print('账号不存在')
            # 保存账号
            save_data = {'mobile': user,
                         'date_created': today_date,
                         'update_created': tomorrow_date}
            mysqlpool_utils.insert_one(connection=mysql_cli, table=self.ss_innojoy_mobile, data=save_data)
        else:
            print('账号已存在')
            # 更新账号数据
            update_data = {'mobile': user,
                         'date_created': today_date,
                         'update_created': tomorrow_date}
            mysqlpool_utils.update(connection=mysql_cli, table=self.ss_innojoy_mobile, data=update_data,
                                   where='mobile="{}"'.format(user))

    #

    # 同步当前页数到redis
    def setInnojoyPage(self, redis_client, key, value):
        redispool_utils.redis_set(redis_client=redis_client, key=key, value=value)

    # 同步当前专利地区分类索引到redis
    def setInnojoyRegionNumber(self, redis_client, key, value):
        redispool_utils.redis_set(redis_client=redis_client, key=key, value=value)

    # 同步当前专利分类索引到redis
    def setInnojoySicNumber(self, redis_client, key, value):
        redispool_utils.redis_set(redis_client=redis_client, key=key, value=value)

    # 同步下一页guid到redis数据库
    def setInnojoyPageGuid(self, redis_client, key, value):
        redispool_utils.redis_set(redis_client=redis_client, key=key, value=value)

    # 从redis获取当前专利分类索引
    def getInnojoySicNumber(self, redis_client, key):
        data = redispool_utils.get(redis_client=redis_client, key=key)
        if data:
            return int(data)
        else:
            return 0

    # 初始化当前专利地区分类索引
    def getInnojoyRegionNumber(self, redis_client, key):
        data = redispool_utils.get(redis_client=redis_client, key=key)
        if data:
            return int(data)
        else:
            return 0

    # 初始化当前在抓页数
    def getInnojoyPage(self, redis_client, key):
        data = redispool_utils.get(redis_client=redis_client, key=key)
        if data:
            return int(data)
        else:
            return 1

    # 初始化下一页页码guid
    def getInnojoyPageGuid(self, redis_client, key):
        data = redispool_utils.get(redis_client=redis_client, key=key)
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
