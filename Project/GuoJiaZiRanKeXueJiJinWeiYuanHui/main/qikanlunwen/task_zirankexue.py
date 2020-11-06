# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import json
import requests
import time
import traceback
import re
from multiprocessing.pool import Pool, ThreadPool
from loguru import logger

# sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../")))

from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"
# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/ZiRanKeXue/论文_task_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口页url
        self.index_url = 'http://ir.nsfc.gov.cn/index/data/getDepartmentInfos'
        self.base_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperQueryForOr'
        self.s = None
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    logger.error('出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def getCatalog(self):
        # 访问入口页
        # self.s = requests.session()
        index_resp = self.__getResp(url=self.index_url, method='GET')
        if not index_resp:
            logger.error('入口页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_resp.encoding = index_resp.apparent_encoding
        index_json = index_resp.json()
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)

        # 获取研究领域名称及列表页种子
        catalog_list = self.server.getCatalogList(json=index_json)
        # print(catalog_list)
        # 列表页进入队列
        self.dao.queue_tasks_to_redis(key=config.REDIS_ZIRANKEXUE_CATALOG, data=catalog_list)

    def getProfile(self, json, xuekeleibie):
        # 提取详情页种子
        next_urls = self.server.getDetailUrl(json=json, xuekeleibie=xuekeleibie)
        # print(next_urls)
        for url in next_urls:
            # 保存url
            self.num += 1
            logger.info('当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=url, ws='国家自然科学基金委员会', es='论文')

    def run(self):
        while 1:
            # 获取任务
            # category_list = self.dao.getTask(key=config.REDIS_ZIRANKEXUE_CATALOG,
            #                                  count=1,
            #                                  lockname=config.REDIS_ZIRANKEXUE_CATALOG_LOCK)
            task_data = self.dao.get_one_task_from_redis(key=config.REDIS_ZIRANKEXUE_CATALOG)
            if task_data:
                try:
                    # 数据类型转换
                    task = json.loads(task_data)
                    # print(task)
                    code = task['code']
                    num = task['num']
                    xueKeLeiBie = task['fieldName']
                    totalCount = task['totalCount']
                    totalPages = int(int(totalCount)/10)

                    # 遍历列表页，获取详情页url
                    for i in range(num, totalPages+1):
                        data = {
                            'query': '',
                            'fieldCode': code,
                            'supportType': '',
                            'organizationID': '',
                            'title': '',
                            'authorID': '',
                            'journalName': '',
                            'orderBy': 'rel',
                            'orderType': 'desc',
                            'year': '',
                            'pageNum': i,
                            'pageSize': 10
                        }

                        # 获取列表页
                        catalog_resp = self.__getResp(url=self.base_url, method='POST', data=json.dumps(data))
                        if not catalog_resp:
                            logger.error('第{}页列表页响应失败, url: {}'.format(i+1, self.base_url))
                            # 队列一条任务
                            task['num'] = i
                            self.dao.queue_one_task_to_redis(key=config.REDIS_ZIRANKEXUE_CATALOG, data=task)
                            break

                        # catalog_resp.encoding = catalog_resp.apparent_encoding
                        try:
                            catalog_json = catalog_resp.json()
                            logger.info('已翻到第{}页'.format(i+1))
                            # print(json.dumps(catalog_json, indent=4, sort_keys=True))

                            # 获取详情url
                            self.getProfile(json=catalog_json, xuekeleibie=xueKeLeiBie)

                        except Exception:
                            logger.error('列表页json内容获取失败')
                            # 队列一条任务
                            task['num'] = i
                            self.dao.queue_one_task_to_redis(key=config.REDIS_ZIRANKEXUE_CATALOG, data=task)
                            return

                    else:
                        logger.info('已翻到最后一页')

                except:
                    logger.exception(str(traceback.format_exc()))

            else:
                logger.info('队列中已无任务，结束程序')

    def start(self):
        # # 创建gevent协程
        # g_list = []
        # for category in category_list:
        #     s = gevent.spawn(self.run, category)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        threadpool = ThreadPool(processes=4)
        for i in range(4):
            threadpool.apply_async(func=self.run)

        threadpool.close()
        threadpool.join()

def process_start():
    main = SpiderMain()
    try:
        # main.getCatalog()
        main.start()
    except:
        logger.error(str(traceback.format_exc()))


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('======Time consuming is %.2fs======' %(end_time - begin_time))
