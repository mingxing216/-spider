# -*-coding:utf-8-*-

'''
知网期刊论文关联机构爬虫
'''
import sys
import os
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from log import log
from utils import redispool_utils
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_jigou_spider
from Project.ZhiWangPeriodicalProject.services import zhiwang_periodical_serveice

logname = 'zhiWangJiGou_spider'
logging = log.ILog(logname)

# redis对象
redis_client = redispool_utils.createRedisPool()
# 爬虫对象
spider = zhiwang_jigou_spider.SpiderMain()
# 服务对象
server = zhiwang_periodical_serveice.ZhiWangJiGouService()



class SpiderMain(object):
    def __init__(self):
        pass

    def handle(self, url):
        return_data = {}
        # 获取机构页html源码
        index_html = spider.getRespForGet(url)
        # 获取sha1
        return_data['sha'] = server.getSha1(url)
        # 获取标题
        return_data['biaoTi'] = server.getJiGouName(index_html)
        # 获取曾用名
        return_data['cengYongMing'] = server.getCengYongMing(index_html)
        # 获取地域
        return_data['diYu'] = server.getDiyu(index_html)
        # 获取官网地址
        return_data['guanWangDiZhi'] = server.getGuanWangDiZhi(index_html)
        # 获取图片
        return_data['tuPian'] = server.getTuPian(index_html)

        print(return_data)

    def spider_run(self, url_list):
        po = ThreadPool(len(url_list))
        for url in url_list:
            po.apply_async(func=self.handle, args=(url,))

        po.close()
        po.join()

    def run(self):
        # # 获取机构任务(100个)
        index_urls = redispool_utils.queue_spops(redis_client=redis_client, key='qikanjigou', lockname='spop_zhiWangJiGou', count=30)
        # # index_url = 'http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield=in&skey=%E5%AE%89%E5%BE%BD%E7%90%86%E5%B7%A5%E5%A4%A7%E5%AD%A6&code=0167619'
        if index_urls:
            self.spider_run(index_urls)





if __name__ == '__main__':
    main = SpiderMain()
    main.run()