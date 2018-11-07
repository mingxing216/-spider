# -*-coding:utf-8-*-

'''
知网期刊论文关联机构爬虫
'''
import sys
import os
import json
import time
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
# from Utils import mysql_dbutils
# from Project.ZhiWangPeriodicalProject.middleware import zhiwang_jigou_spider
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider
from Project.ZhiWangPeriodicalProject.services import serveice
from Project.ZhiWangPeriodicalProject.dao import sql_dao

log_file_dir = 'zhiWangJiGou_spider_main'
LOGNAME = '<期刊_机构爬虫>'
LOGGING = log.ILog(log_file_dir, LOGNAME)


# 爬虫对象
# spider = zhiwang_jigou_spider.SpiderMain()
spider = zhiwang_periodical_spider.SpiderMain()
# 服务对象
server = serveice.ZhiWangJiGouService()

class SpiderMain(object):
    def __init__(self):
        pass

    def handle(self, redis_client, mysql_client, url):
        return_data = {}
        sha = server.getSha1(url)
        # 获取机构页html源码
        index_html = spider.getRespForGet(redis_client=redis_client, url=url, logging=LOGGING)
        # 获取sha1
        return_data['sha'] = sha
        # 获取地域
        return_data['suoZaiDiNeiRong'] = server.getDiyu(index_html)
        # 生成ws字段
        return_data['ws'] = '中国知网'
        # 生成biz字段
        return_data['biz'] = '文献大数据'
        # 生成url字段
        return_data['url'] = url
        # 获取曾用名
        return_data['cengYongMing'] = server.getCengYongMing(index_html)
        # 生成ref字段
        return_data['ref'] = url
        # 获取官网地址
        return_data['zhuYe'] = server.getGuanWangDiZhi(index_html)
        # 获取标题
        return_data['title'] = server.getJiGouName(index_html)
        # 生成ss字段
        return_data['ss'] = '机构'
        # 生成es字段
        return_data['es'] = '期刊论文'
        # 生成clazz字段
        return_data['clazz'] = '企业机构'
        # 生成key字段
        return_data['key'] = url
        # 获取图片
        return_data['biaoShi'] = server.getTuPian(index_html)

        title = return_data['title']
        return_data = json.dumps(return_data)

        # 数据入库
        sql_dao.saveJiGou(mysql_client=mysql_client, sha=sha, title=title, data=return_data, logging=LOGGING)


    def spider_run(self,redis_client, mysql_client, url_list):
        po = ThreadPool(10)
        for url in url_list:
            po.apply_async(func=self.handle, args=(redis_client, mysql_client, url))

        po.close()
        po.join()

    def run(self):
        # redis对象
        redis_client = redispool_utils.createRedisPool()
        # mysql对象
        mysql_client = mysqlpool_utils.createMysqlPool()
        while True:
            # 获取机构任务(100个)
            index_urls = redispool_utils.queue_spops(redis_client=redis_client, key='qikanjigou', lockname='spop_zhiwang_jigou', count=100)
            if index_urls:
                self.spider_run(redis_client=redis_client, mysql_client=mysql_client, url_list=index_urls)
            else:
                LOGGING.error('机构队列无任务， 程序睡眠300秒')
                time.sleep(300)


if __name__ == '__main__':
    main = SpiderMain()
    po = Pool(int(settings.ZHIWANG_JIGOU_SPIDER_PROCESS))
    for i in range(int(settings.ZHIWANG_JIGOU_SPIDER_PROCESS)):
        po.apply_async(func=main.run)
    po.close()
    po.join()