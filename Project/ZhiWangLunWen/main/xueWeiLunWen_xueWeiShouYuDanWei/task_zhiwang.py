# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<学位论文_学位授予单位_task>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.XueWeiLunWen_xueWeiShouYuDanWei(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_MAX_NUMBER,
                           redispool_number=config.REDIS_POOL_MAX_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 地域导航页url
        self.index_url = 'http://navi.cnki.net/knavi/Common/LeftNavi/PPaper'
        # 单位列表页url
        self.page_url = 'http://navi.cnki.net/knavi/Common/Search/PPaper'
        self.num = 0


    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        resp = None
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return resp

    def getCategory(self):
        # 生成导航栏页面post请求参数
        index_url_data = self.server.get_index_url_data()
        # print(index_url_data)
        # 获取地域导航页响应
        index_resp = self.__getResp(url=self.index_url, method='POST', data=index_url_data)
        # print(index_resp.text)
        if not index_resp:
            LOGGING.error('学位授予单位地域导航页接口响应失败')
            return
        index_text = index_resp.text
        # 获取分类参数
        catalog_list = self.server.get_fen_lei_data_list(resp=index_text)
        # print(catalog_list)
        # 列表页参数进入队列
        self.dao.queue_tasks_to_redis(key=config.REDIS_XUEWEI_CATEGORY, data=catalog_list)

    def run(self, category):
        # 数据类型转换
        task = self.server.get_eval(category)
        para = task['data']
        totalCount = int(task['totalCount'])
        num = int(task['num'])

        # 获取总页数
        page_number = self.server.get_page_number(totalCount=totalCount)
        for page in range(num, page_number+1):
            data = self.server.get_dan_wei_list_url_data(data=para, page=page)
            # 获取列表页响应
            catalog_resp = self.__getResp(url=self.page_url, method='POST', data=data)
            if not catalog_resp:
                LOGGING.error('学位授予单位列表第{}页接口响应失败, url: {}'.format(page, self.page_url))
                # 队列一条任务
                task['num'] = page
                self.dao.queue_one_task_to_redis(key=config.REDIS_XUEWEI_CATEGORY, data=task)
                return
            catalog_resp.encoding = catalog_resp.apparent_encoding
            catalog_text = catalog_resp.text
            # 获取单位url
            para_value = self.server.get_eval(para)
            danwei_url_list = self.server.get_dan_wei_url_list(resp=catalog_text, value=para_value[2])
            # print(danwei_url_list)
            # 学位授予单位详情页作为二级分类页进入redis队列
            self.dao.queue_tasks_to_redis(key=config.REDIS_XUEWEI_CATALOG, data=danwei_url_list)
            for danwei_url in danwei_url_list:
                # 保存url
                self.num += 1
                LOGGING.info('当前已抓学位授予单位种子数量: {}'.format(self.num))
                # 数据存储
                self.dao.save_task_to_mysql(table=config.MYSQL_INSTITUTE, memo=danwei_url, ws='中国知网', es='学位论文')
                # LOGGING.info(danwei_url)
                # print(danwei_url)

    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.get_task_from_redis(key=config.REDIS_XUEWEI_CATEGORY,
                                                         count=50,
                                                         lockname=config.REDIS_XUEWEI_CATEGORY_LOCK)
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
        # main.run("{'data': \"('1','AREANAME','0002','北京市')\", 'totalCount': '159', 'num': 1}")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
