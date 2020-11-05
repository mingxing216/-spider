# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import requests
import time
import traceback
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.YuBoBaoGao.middleware import download_middleware
from Project.YuBoBaoGao.service import service
from Project.YuBoBaoGao.dao import dao
from Project.YuBoBaoGao import config

log_file_dir = 'YuBo'  # LOG日志存放路径
LOGNAME = '<宇博_报告_task>'  # LOG名
NAME = '宇博_报告_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


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
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口页url
        self.index_url = 'http://www.chinabgao.com/'
        # 获取最小级分类号
        self.category = []
        self.cookie_dict = ''
        self.cookie_str = ''
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def getCategory(self):
        # 访问入口页
        index_resp = self.__getResp(url=self.index_url,
                                    method='GET')
        if not index_resp:
            LOGGING.error('入口页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_resp.encoding = index_resp.apparent_encoding
        index_text = index_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)

        # 获取行业名称及种子分类列表
        industry_list = self.server.getIndustryList(resp=index_text)
        if industry_list:
            for industry in industry_list:
                industry_url = industry['url']
                hangYe = industry['s_hangYe']
                industry_resp = self.__getResp(url=industry_url,
                                               method='GET')
                if not industry_resp:
                    LOGGING.error('行业分类页响应失败, url: {}'.format(industry_url))
                    # industry_list.append(industry)
                    continue

                industry_resp.encoding = industry_resp.apparent_encoding
                industry_text = industry_resp.text

                # 获取研究领域分类列表
                field_list = self.server.getFieldList(resp=industry_text, hangye=hangYe)
                # 列表页进入队列
                self.dao.queue_tasks_to_redis(key=config.REDIS_YUBO_CATEGORY, data=field_list)
        #         # 列表页存入变量
        #         for field in field_list:
        #             self.category.append(field)
        #             # 存入数据库
        #             self.dao.saveTaskToMysql(table=config.MYSQL_REPORT, memo=field, ws='宇博报告大厅', es='列表页')
        #
        # print(self.category)
        # print(len(self.category))


    def getProfile(self, resp, hangye, leixing):
        next_resp = resp
        next_num = 2

        while True:
            # 响应成功，提取详情页种子
            next_text = next_resp.text
            next_urls = self.server.getDetailUrl(resp=next_text, hangye=hangye, leixing=leixing)
            # print(next_urls)
            for url in next_urls:
                # 保存url
                self.num += 1
                LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                # 存入数据库
                self.dao.save_task_to_mysql(table=config.MYSQL_REPORT, memo=url, ws='宇博报告大厅', es='行业研究报告')

            # 判断是否有下一页
            next_url = self.server.hasNextUrl(resp=next_text)
            # print(next_url)
            # 如果有，请求下一页，获得响应
            if next_url:
                # 获取下一页响应
                next_resp = self.__getResp(url=next_url, method='GET')

                # 如果响应获取失败，队列这一页种子到redis
                if not next_resp:
                    LOGGING.error('列表页第{}页响应失败, url: {}'.format(next_num, next_url))
                    next_dict = {}
                    next_dict['url'] = next_url
                    next_dict['s_hangYe'] = hangye
                    next_dict['s_leiXing'] = leixing
                    return

                # 响应成功，添加log日志
                LOGGING.info('已翻到第{}页'.format(next_num))

                next_num += 1

            else:
                LOGGING.info('已翻到最后一页')
                break


    def run(self, category):
        # 数据类型转换
        task = self.server.getEvalResponse(category)
        url = task['url']
        hangye = task['s_hangYe']
        leixing = task['s_leiXing']

        # # 创建cookie
        # self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
        # if not self.cookie_dict:
        #     # 队列一条任务
        #     self.dao.QueueOneTask(key=config.REDIS_XX_CATEGORY, data=category)
        #     return

        # 获取列表首页响应
        first_resp = self.__getResp(url=url, method='GET')
        if not first_resp:
            LOGGING.error('列表首页响应失败, url: {}'.format(url))
            # 队列一条任务
            self.dao.queue_one_task_to_redis(key=config.REDIS_YUBO_CATEGORY, data=task)
            return

        # 获取详情url
        self.getProfile(resp=first_resp, hangye=hangye, leixing=leixing)


    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.get_task_from_redis(key=config.REDIS_YUBO_CATEGORY,
                                                         count=10,
                                                         lockname=config.REDIS_YUBO_CATEGORY_LOCK)
            # print(category_list)
            LOGGING.info('获取{}个任务'.format(len(category_list)))

            if category_list:
                # 创建gevent协程
                g_list = []
                for category in category_list:
                    s = gevent.spawn(self.run, category)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for category in category_list:
                #     threadpool.apply_async(func=self.run, args=(category,))
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
        main.getCategory()
        main.start()
        # main.run('{"url": "http://www.chinabgao.com/report/c_led/", "s_hangYe": "IT_液晶产业", "s_leiXing": "不限"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
