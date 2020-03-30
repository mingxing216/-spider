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
from Project.ShangWuBu.middleware import download_middleware
from Project.ShangWuBu.service import service
from Project.ShangWuBu.dao import dao
from Project.ShangWuBu import config

log_file_dir = 'ShangWuBu'  # LOG日志存放路径
LOGNAME = '<商务部_中国商务法规_task>'  # LOG名
NAME = '商务部_中国商务法规_task'  # 爬虫名
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
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 入口页url列表
        self.index_list = [
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=1&sortName=%E6%B3%95%E5%BE%8B&fg=2",
                "es": "法律", "clazz": "法律法规_中国内地法律法规_中央法律法规_宪法法律"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=2&sortName=%E8%A1%8C%E6%94%BF%E6%B3%95%E8%A7%84&fg=2",
                "es": "行政法规", "clazz": "法律法规_中国内地法律法规_中央法律法规_行政法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=9&sortName=%E5%9B%BD%E5%8A%A1%E9%99%A2%E8%A7%84%E8%8C%83%E6%80%A7%E6%96%87%E4%BB%B6&fg=2",
                "es": "国务院规范性文件", "clazz": "法律法规_中国内地法律法规_中央法律法规_行政法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=3&sortName=%E5%8F%B8%E6%B3%95%E8%A7%A3%E9%87%8A&fg=2",
                "es": "司法解释", "clazz": "法律法规_中国内地法律法规_中央法律法规_司法解释"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=7&sortName=%E5%8F%B8%E6%B3%95%E8%A7%A3%E9%87%8A%E6%80%A7%E8%B4%A8%E6%96%87%E4%BB%B6&fg=2",
                "es": "司法解释性质文件", "clazz": "法律法规_中国内地法律法规_中央法律法规_司法解释"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=4&sortName=%E9%83%A8%E9%97%A8%E8%A7%84%E7%AB%A0&fg=2",
                "es": "部门规章", "clazz": "法律法规_中国内地法律法规_中央法律法规_部门规章"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=5&sortName=%E9%83%A8%E9%97%A8%E8%A7%84%E8%8C%83%E6%80%A7%E6%96%87%E4%BB%B6&fg=2",
                "es": "部门规范性文件", "clazz": "法律法规_中国内地法律法规_中央法律法规_部门规章"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=8&sortName=%E8%A1%8C%E4%B8%9A%E8%A7%84%E5%AE%9A&fg=2",
                "es": "行业规定", "clazz": "法律法规_中国内地法律法规_中央法律法规_行业规定"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=11&sortName=%E7%9C%81%E7%BA%A7%E5%9C%B0%E6%96%B9%E6%80%A7%E6%B3%95%E8%A7%84&fg=2",
                "es": "省级地方性法规", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方性法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=10&sortName=%E5%9C%B0%E6%96%B9%E6%94%BF%E5%BA%9C%E8%A7%84%E7%AB%A0&fg=2",
                "es": "地方政府规章", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方政府规章"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=12&sortName=%E5%9C%B0%E6%96%B9%E8%A7%84%E8%8C%83%E6%80%A7%E6%96%87%E4%BB%B6&fg=2",
                "es": "地方规范性文件", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方规范性文件"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=13&sortName=%E8%AE%BE%E5%8C%BA%E7%9A%84%E5%B8%82%E5%9C%B0%E6%96%B9%E6%80%A7%E6%B3%95%E8%A7%84&fg=2",
                "es": "设区的市地方性法规", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方性法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=14&sortName=%E5%9C%B0%E6%96%B9%E6%80%A7%E6%B3%95%E8%A7%84&fg=2",
                "es": "地方性法规", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方性法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=15&sortName=%E8%87%AA%E6%B2%BB%E6%9D%A1%E4%BE%8B%E5%92%8C%E5%8D%95%E8%A1%8C%E6%9D%A1%E4%BE%8B&fg=2",
                "es": "自治条例和单行条例", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方性法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=16&sortName=%E7%BB%8F%E6%B5%8E%E7%89%B9%E5%8C%BA%E6%B3%95%E8%A7%84&fg=2",
                "es": "经济特区法规", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方性法规"},
            {
                "url": "http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?sortId=17&sortName=%E5%9C%B0%E6%96%B9%E5%8F%B8%E6%B3%95%E6%96%87%E4%BB%B6&fg=2",
                "es": "地方司法文件", "clazz": "法律法规_中国内地法律法规_地方法规规章_地方司法文件"}
        ]
        # 年列表
        self.year_url = 'http://policy.mofcom.gov.cn/claw/keySearchMore.shtml?xiaoliTp={}&sortId={}&sortName={}&fg={}'
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
        # 遍历入口页列表
        for index in self.index_list:
            index_url = index['url']
            es = index['es']
            clazz = index['clazz']
            id = self.server.getId(index_url)
            index_resp = self.__getResp(url=index_url, method='GET')
            if not index_resp:
                LOGGING.error('入口页面响应失败, url: {}'.format(index_url))
                return
            # 遵循网页原本编码方式
            index_resp.encoding = index_resp.apparent_encoding
            index_text = index_resp.text
            # with open ('index.html', 'w') as f:
            #     f.write(index_text)
            # return
            # 获取年列表
            year_list = self.server.getYearList(resp=index_text, id=id, year_url=self.year_url, es=es, clazz=clazz, para='发布时间')
            # 列表页进入队列
            self.dao.QueueJobTask(key=config.REDIS_SHANGWUBU_FAGUI, data=year_list)
            # print(year_list)
            # print(len(year_list))

    def getProfile(self, first_text, task, nianfen, es, clazz):
        # 判断是否有下一页
        total_num = self.server.totalPages(resp=first_text)
        # print(total_num)
        # 如果有，请求下一页，获得响应
        if int(total_num) > 1:
            for i in range(2, int(total_num) + 1):
                next_url = task['url'] + '&pageNum=' + str(i)
                # 获取下一页响应
                next_resp = self.__getResp(url=next_url, method='GET')

                # 如果响应获取失败，队列这一页种子到redis
                if not next_resp:
                    LOGGING.error('列表页第{}页响应失败, url: {}'.format(i, next_url))
                    task['url'] = next_url
                    self.dao.QueueOneTask(key=config.REDIS_SHANGWUBU_TIAOYUE, data=task)
                    return

                # 响应成功，添加log日志
                LOGGING.info('已翻到第{}页'.format(i))

                # 遵循网页原本编码方式
                next_resp.encoding = next_resp.apparent_encoding
                # 响应成功，提取详情页种子
                next_text = next_resp.text
                next_urls = self.server.getDetailUrl(resp=next_text, nianfen=nianfen, es=es, clazz=clazz)
                # print(next_urls)
                for url in next_urls:
                    # 保存url
                    self.num += 1
                    LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                    # 存入数据库
                    self.dao.saveTaskToMysql(table=config.MYSQL_LAW, memo=url, ws='中华人民共和国商务部', es='中国商务法规')
            else:
                LOGGING.info('已翻到最后一页')

        else:
            LOGGING.info('已翻到最后一页')

    def run(self, category):
        # 数据类型转换
        task = self.server.getEvalResponse(category)
        url = task['url']
        nianfen = task['nianfen']
        es = task['es']
        clazz = task['clazz']

        # 获取列表首页响应
        first_resp = self.__getResp(url=url, method='GET')
        if not first_resp:
            LOGGING.error('列表首页响应失败, url: {}'.format(url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_SHANGWUBU_FAGUI, data=task)
            return

        # 遵循网页原本编码方式
        first_resp.encoding = first_resp.apparent_encoding
        # 响应成功，提取详情页种子
        first_text = first_resp.text
        first_urls = self.server.getDetailUrl(resp=first_text, nianfen=nianfen, es=es, clazz=clazz)
        # print(first_urls)
        for url in first_urls:
            # 保存url
            self.num += 1
            LOGGING.info('当前已抓种子数量: {}'.format(self.num))
            # 存入数据库
            self.dao.saveTaskToMysql(table=config.MYSQL_LAW, memo=url, ws='中华人民共和国商务部', es='中国商务法规')
        # 获取详情url
        self.getProfile(first_text=first_text, task=task, nianfen=nianfen, es=es, clazz=clazz)

    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_SHANGWUBU_FAGUI,
                                             count=10,
                                             lockname=config.REDIS_SHANGWUBU_FAGUI_LOCK)
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

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
