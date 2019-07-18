# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.IHSmarkit.middleware import download_middleware
from Project.IHSmarkit.service import service
from Project.IHSmarkit.dao import dao
from Project.IHSmarkit import config

log_file_dir = 'IHSmarkit'  # LOG日志存放路径
LOGNAME = '<IHSmarkit_标准_task>'  # LOG名
NAME = 'IHSmarkit_标准_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口种子
        self.index_url = 'https://global.ihs.com/standards.cfm?&rid=IHS'
        # 列表页种子存放列表
        self.catalog_url_list = []

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    def start(self):
        # 访问发布单位列表页
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('发布单位页面响应获取失败, url: {}'.format(self.index_url))
            # # 队列一条任务
            # self.dao.QueueOneTask(key=config.REDIS_YEAR, data=self.index_url)
            return

        index_text = index_resp.text

        # 获取列表中的发布单位url
        publish_url_list = self.server.getPublishUrlList(resp=index_text)
        # return
        if not publish_url_list:
            return

        print(publish_url_list)

        # 访问每个发布单位url，获取列表页种子
        for publish_url in publish_url_list:
            # 访问发布单位详情页
            catalog_resp = self.__getResp(func=self.download_middleware.getResp,
                                        url=publish_url,
                                        mode='GET')
            if not catalog_resp:
                LOGGING.error('列表页响应获取失败, url: {}'.format(publish_url))
                # # 队列一条任务
                # self.dao.QueueOneTask(key=config.REDIS_YEAR, data=publish_url)
                return

            catalog_text = catalog_resp.text

            # 获取列表页种子
            catalog_url = self.server.getCatalogUrl(resp=catalog_text)
            print(catalog_url)
            self.catalog_url_list.append(catalog_url)

        # 队列任务
        self.dao.QueueJobTask(key=config.REDIS_YEAR, data=self.catalog_url_list)



def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(1)
    for i in range(1):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
