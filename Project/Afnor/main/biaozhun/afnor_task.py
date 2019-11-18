# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Afnor.middleware import download_middleware
from Project.Afnor.service import service
from Project.Afnor.dao import dao
from Project.Afnor import config

log_file_dir = 'Afnor'  # LOG日志存放路径
LOGNAME = 'Afnor_标准_task'  # LOG名
NAME = 'Afnor_标准_task'  # 爬虫名
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
        self.index_url = 'https://www.boutique.afnor.org/search/results/category/standards'
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
        # 访问入口页，获取所有出版商
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('入口页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)
        # return

        # 获取标准类型分类种子
        type_url = self.server.getClassifyUrl(resp=index_text, para='Type of document')
        if not type_url:
            return

        print(type_url)

        # 访问标准类型url，获取列表页url及分类字段
        type_resp = self.__getResp(func=self.download_middleware.getResp,
                                       url=type_url,
                                       mode='GET')
        if not type_resp:
            LOGGING.error('页面响应失败, url: {}'.format(type_url))
            return

        type_text = type_resp.text

        type_list = self.server.getCatalogUrl(resp=type_text, key='s_标准类型')
        # print(type_list)
        print(len(type_list))
        # 进入队列
        self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=type_list)

        # 获取行业分类种子
        sector_url = self.server.getClassifyUrl(resp=index_text, para='SECTOR')
        if not sector_url:
            return

        print(sector_url)

        # 访问行业url，获取列表页url及分类字段
        sector_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=sector_url,
                                    mode='GET')
        if not sector_resp:
            LOGGING.error('页面响应失败, url: {}'.format(sector_url))
            return

        sector_text = sector_resp.text

        sector_list = self.server.getCatalogUrl(resp=sector_text, key='s_行业')
        # print(sector_list)
        print(len(sector_list))
        # 进入队列
        self.dao.QueueJobTask(key=config.REDIS_CATALOG, data=sector_list)

    def run(self, task):
        catalog_url = ''
        classify = ''
        classifu_value = ''
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        for k in task_data:
            if k == 'url':
                catalog_url = task_data[k]
            else:
                classify = k
                classifu_value = task_data[k]

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

        # with open ('prifile.html', 'w') as f:
        #     f.write(first_resp.text)

        # 获取首页详情url
        first_urls = self.server.getDetailUrl(resp=first_resp.text, k=classify, v=classifu_value)
        # print(first_urls)
        print(len(first_urls))
        for url in first_urls:
            # 保存url
            self.num += 1
            LOGGING.info('当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_STANDARD, memo=url, ws='AFNOR', es='标准')

        # 获取列表页总页数
        total_page = self.server.getTotalPage(resp=first_resp.text)

        # 如果有，请求下一页，获得响应
        if int(total_page) > 1:
            for i in range(2, int(total_page) + 1):
                next_url = catalog_url + '?page=' + str(i)

                next_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=next_url,
                                           mode='GET')

                # 如果响应获取失败，重新访问，并记录这一页种子
                if not next_resp:
                    LOGGING.error('第{}页响应获取失败, url: {}'.format(i, next_url))
                    # 队列一条任务
                    self.dao.QueueOneTask(key=config.REDIS_CATALOG, data=next_url)
                    continue
                # 响应成功，添加log日志
                LOGGING.info('已翻到第{}页'.format(i))

                # 获得响应成功，提取详情页种子
                next_text = next_resp.text
                next_urls = self.server.getDetailUrl(resp=next_text, k=classify, v=classifu_value)
                # print(next_urls)
                print(len(next_urls))
                for url in next_urls:
                    # 保存url
                    self.num += 1
                    LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.dao.saveTaskToMysql(table=config.MYSQL_STANDARD, memo=url, ws='AFNOR', es='标准')

        else:
            LOGGING.info('已翻到最后一页')


    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_CATALOG,
                                         count=1,
                                         lockname=config.REDIS_CATALOG_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # # 创建gevent协程
                # g_list = []
                # for task in task_list:
                #     s = gevent.spawn(self.run, task)
                #     g_list.append(s)
                # gevent.joinall(g_list)

                # 创建线程池
                threadpool = ThreadPool()
                for url in task_list:
                    threadpool.apply_async(func=self.run, args=(url,))

                threadpool.close()
                threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

def process_start():
    main = SpiderMain()
    try:
        # 获取列表页并使之进入队列
        # main.getCatalog()
        # 获取详情页
        main.start()
        # main.run("https://www.mystandards.biz/publisher/astm-standards-adjuncts-reference-radiographs/")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
