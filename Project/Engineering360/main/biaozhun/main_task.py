# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import gevent
from gevent import monkey
# 猴子补丁一定要先打，不然就会报错
monkey.patch_all()

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Engineering360.middleware import download_middleware
from Project.Engineering360.service import service
from Project.Engineering360.dao import dao
from Project.Engineering360 import config

log_file_dir = 'Engineering360'  # LOG日志存放路径
LOGNAME = 'Engineering360_标准_task'  # LOG名
NAME = 'Engineering360_标准_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.BiaoZhunServer(logging=LOGGING)
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
        self.index_url = 'https://standards.globalspec.com/stds/sdo'
        # 列表页种子存放列表
        self.catalog_url_list = []
        # 记录已存储种子数量
        self.num = 0

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None

    def getCatalog(self):
        # 访问发布单位列表页
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('发布单位列表页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text

        # 获取列表页
        publish_url_list = self.server.getPublishUrlList(resp=index_text)
        if not publish_url_list:
            return

        # print(publish_url_list)
        print(len(publish_url_list))

        # 遍历列表页，存入列表
        for publish in publish_url_list:
            self.catalog_url_list.append(publish)

        print(len(self.catalog_url_list))
        # 队列任务
        self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=self.catalog_url_list)

    def run(self, catalog_url):
        # 请求列表页，获取首页响应
        first_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=catalog_url,
                                    mode='GET')
        if not first_resp:
            LOGGING.error('列表首页响应获取失败, url: {}'.format(catalog_url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=catalog_url)
            return
        # 响应成功，添加log日志
        LOGGING.info('已进入列表第1页')
        # 获取首页详情url
        first_urls = self.server.getDetailUrl(resp=first_resp.text)
        for url in first_urls:
            # 保存url
            self.num += 1
            LOGGING.info('当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_STANTARD, memo=url, ws='Engineering360', es='标准')
            # detail_urls.append(url)

        # 判断是否有下一页
        next_page = self.server.hasNextPage(resp=first_resp.text)

        # 如果有，请求下一页，获得响应
        if next_page:
            for i in range(2, int(next_page) + 1):
                next_url = catalog_url + '?pg=' + str(i)

                next_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=next_url,
                                           mode='GET')

                # 如果响应获取失败，重新访问，并记录这一页种子
                if not next_resp:
                    LOGGING.error('第{}页响应获取失败, url: {}'.format(i, next_url))
                    # 队列任务
                    self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=next_url)
                    continue
                # 响应成功，添加log日志
                LOGGING.info('已翻到第{}页'.format(i))

                # 获得响应成功，提取详情页种子
                next_text = next_resp.text
                next_urls = self.server.getDetailUrl(resp=next_text)
                # print(next_urls)
                for url in next_urls:
                    # 保存url
                    self.num += 1
                    LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.dao.saveTaskToMysql(table=config.MYSQL_STANTARD, memo=url, ws='Engineering360', es='标准')
                    # detail_urls.append(url)

            # print(len(detail_urls))

        else:
            LOGGING.info('已翻到最后一页')

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_CATALOG,
                                         count=10,
                                         lockname=config.REDIS_CATALOG_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

def process_start():
    main = SpiderMain()
    try:
        # 获取列表页并使之进入队列
        main.getCatalog()
        # 获取详情页
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
