# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import json
import requests
import traceback
import multiprocessing
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<学位论文_论文_task>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                 proxy_type=config.PROXY_TYPE,
                                                                 timeout=config.TIMEOUT)
        self.server = service.XueWeiLunWen_LunWen(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_MAX_NUMBER,
                           redispool_number=config.REDIS_POOL_MAX_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 索引页
        self.index_url = 'https://navi.cnki.net/KNavi/PPaper.html?productcode=CDFD'
        # 列表首页url
        self.page_number_url = 'https://navi.cnki.net/knavi/PPaperDetail/GetArticleBySubject'
        # 翻页url
        self.lunwen_list_url = 'https://navi.cnki.net/knavi/PPaperDetail/GetArticleBySubjectinPage'
        # 会话
        self.s = requests.Session()
        # 记录存储种子数量
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        resp = None
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return resp

    def get_Profile(self, url, page, catalog, value, task):
        # 获取列表页请求参数
        data = self.server.getLunWenPageData(url, page, catalog['zhuanYeId'])
        print(data)
        while True:
            # 获取列表页响应
            lunwen_list_resp = self.__getResp(s=self.s, url=self.lunwen_list_url, method='POST', data=data)
            if not lunwen_list_resp:
                LOGGING.error('论文列表页第{}页响应获取失败，url: {}, data: {}'.format(page+1, self.lunwen_list_url, data))
                # 队列一条任务
                self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
                return
            # 处理验证码
            if '请输入验证码' in lunwen_list_resp.text or len(lunwen_list_resp.text) < 10:
                LOGGING.error('出现验证码,重新建立会话')
                # 创建cookies
                cookies = self.download_middleware.create_cookie(url=url)
                if not cookies:
                    # 队列一条任务
                    self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
                    return
                self.s.cookies = cookies
                # self.download_middleware.getFenLei(s=self.s, value=value)
                # self.__getResp(s=self.s, url=url, method='GET', referer=self.index_url)
                continue
            else:
                break
        LOGGING.info('已翻到第{}页'.format(page+1))
        # lunwen_list_resp.encoding = lunwen_list_resp.apparent_encoding
        lunwen_list_text = lunwen_list_resp.text
        # 获取论文队列参数
        lunwen_url_list = self.server.getProfileUrl(resp=lunwen_list_text, zhuanye=catalog['s_zhuanYe'], parent_url=url)
        for lunwen_url_data in lunwen_url_list:
            # 保存数据
            self.num += 1
            LOGGING.info('已抓种子数量: {}'.format(self.num))
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen_url_data, ws='中国知网', es='学位论文')

    def handle(self, catalog, url, task):
        print(catalog)
        value = catalog.get('value')
        # 获取专业列表页post参数
        zhuanye_post_data = self.server.getZhuanYeData(url=url, data=catalog)
        # print(zhuanye_post_data)
        while True:
            # 获取列表页响应
            catalog_resp = self.__getResp(s=self.s, url=self.page_number_url, method='POST', data=zhuanye_post_data)
            if not catalog_resp:
                LOGGING.error('论文列表页首页响应获取失败，url: {}, data: {}'.format(self.lunwen_list_url, zhuanye_post_data))
                # 队列一条任务
                self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
                return
            # 处理验证码
            if '请输入验证码' in catalog_resp.text or len(catalog_resp.text) < 10:
                LOGGING.error('出现验证码,重新建立会话')
                # 创建cookies
                cookies = self.download_middleware.create_cookie(url=url)
                if not cookies:
                    # 队列一条任务
                    self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
                    return
                self.s.cookies = cookies
                # self.download_middleware.getFenLei(s=self.s, value=value)
                # self.__getResp(s=self.s, url=url, method='GET', referer=self.index_url)
                continue
            else:
                break
        # catalog_resp.encoding = catalog_resp.apparent_encoding
        catalog_text = catalog_resp.text
        LOGGING.info('已翻到第一页')
        # 获取论文队列参数
        lunwen_url_list = self.server.getProfileUrl(resp=catalog_text, zhuanye=catalog['s_zhuanYe'], parent_url=url)
        for lunwen_url_data in lunwen_url_list:
            # 保存数据
            self.num += 1
            LOGGING.info('已抓种子数量: {}'.format(self.num))
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=lunwen_url_data, ws='中国知网', es='学位论文')
        # 获取列表页总页数
        totalPage = self.server.getPageNumber(resp=catalog_text)
        # print(totalPage)
        if totalPage > 1:
            for page in range(1, int(totalPage)):
                self.get_Profile(url, page, catalog, value, task)
            else:
                LOGGING.info('已翻到最后一页')
        else:
            LOGGING.info('已翻到最后一页')

    def run(self, category):
        # 数据类型转换
        task = self.server.getEvalResponse(category)
        print(task)
        url = task['url']
        value = task.get('value')

        # 创建cookies
        cookies = self.download_middleware.create_cookie(url=url)
        if not cookies:
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
            return
        # 设置会话cookies
        self.s.cookies = cookies
        # # 逐步访问授予单位分类接口，防止出现验证码
        # self.download_middleware.getFenLei(s=self.s, value=value)
        # self.__getResp(s=self.s, url=url, method='GET')

        # 生成专业列表页url
        zhuanye_url = self.server.getXueKeZhuanYe(url=url)
        # print(zhuanye_url)
        # 获取专业列表页响应
        zhuanye_resp = self.__getResp(s=self.s, url=zhuanye_url, method='GET')
        if not zhuanye_resp:
            LOGGING.error('学科专业分类接口响应失败, url: {}'.format(zhuanye_url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_XUEWEI_CATALOG, data=task)
            return
        # zhuanye_resp.encoding = zhuanye_resp.apparent_encoding
        zhuanye_text = zhuanye_resp.text
        # 获取学科专业列表
        zhuanye_list = self.server.getZhuanYeList(resp=zhuanye_text, value=value)
        # print(zhuanye_list)
        # 遍历学科专业列表，获取详情页
        for catalog in zhuanye_list:
            self.handle(catalog, url, task)

    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_XUEWEI_CATALOG,
                                             count=1,
                                             lockname=config.REDIS_XUEWEI_CATALOG_LOCK)
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
        main.start()
        # main.run("{'url': 'https://navi.cnki.net/knavi/PPaperDetail?pcode=CDMD&logo=GJZSC', 'value': '0018'}")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
