# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangPapers.middleware import download_middleware
from Project.ZhiWangPapers.service import service
from Project.ZhiWangPapers.dao import dao
from Project.ZhiWangPapers import config

log_file_dir = 'ZhiWangPapers'  # LOG日志存放路径
LOGNAME = '<知网期刊机构数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.JiGouDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.JiGouServer(logging=LOGGING)
        self.dao = dao.JiGouDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化机构redis集合名
        self.qikanjigou = 'qikanjigou'
        # 初始化redis分布式锁名
        self.redis_lockname = 'spop_zhiwang_jigou'

    def handle(self, url):
        return_data = {}
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 获取机构页html源码
        index_html = self.download_middleware.getResp(url=url)
        if index_html['status'] == 0:
            resp = index_html['data'].content.decode('utf-8')
            # 获取sha1
            return_data['sha'] = sha
            # 获取地域
            return_data['suoZaiDiNeiRong'] = self.server.getDiyu(resp)
            # 生成ws字段
            return_data['ws'] = '中国知网'
            # 生成biz字段
            return_data['biz'] = '文献大数据'
            # 生成url字段
            return_data['url'] = url
            # 获取曾用名
            return_data['cengYongMing'] = self.server.getCengYongMing(resp)
            # 生成ref字段
            return_data['ref'] = url
            # 获取官网地址
            return_data['zhuYe'] = self.server.getGuanWangDiZhi(resp)
            # 获取标题
            return_data['title'] = self.server.getJiGouName(resp)
            # 生成ss字段
            return_data['ss'] = '机构'
            # 生成es字段
            return_data['es'] = '期刊论文'
            # 生成clazz字段
            return_data['clazz'] = '企业机构'
            # 生成key字段
            return_data['key'] = url
            # 获取图片
            return_data['biaoShi'] = self.server.getTuPian(resp)

            # 数据入库
            status = self.dao.saveDataToHbase(data=return_data)
            LOGGING.info(status.content.decode('utf-8'))

        else:
            LOGGING.error('机构页html源码获取失败')

    def spider_run(self, url_list):
        po = ThreadPool(1)
        for url in url_list:
            po.apply_async(func=self.handle, args=(url, ))
        po.close()
        po.join()

    def start(self):
        while 1:
            # 获取机构任务(100个)
            index_urls = self.dao.getIndexUrls(key=self.qikanjigou, lockname=self.redis_lockname)
            if index_urls:
                self.spider_run(url_list=index_urls)

            else:
                LOGGING.error('机构队列无任务， 程序睡眠300秒')
                time.sleep(300)

            break


def process_start():
    main = SpiderMain()
    main.start()

if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANG_JIGOU_SPIDER_PROCESS)
    for i in range(config.ZHIWANG_JIGOU_SPIDER_PROCESS):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
