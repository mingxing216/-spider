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
LOGNAME = '<商务部_中外条约_task>'  # LOG名
NAME = '商务部_中外条约_task'  # 爬虫名
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
        # 入口页url
        self.index_list = [
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=1&sortName=%E5%85%AC%E7%BA%A6&fg=2",
                "es": "公约", "clazz": "法律法规_国际条约_公约"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=2&sortName=%E8%AE%AE%E5%AE%9A%E4%B9%A6&fg=2",
                "es": "议定书", "clazz": "法律法规_国际条约_议定书"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=3&sortName=%E5%8D%8F%E5%AE%9A&fg=2",
                "es": "协定", "clazz": "法律法规_国际条约_协定"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=5&sortName=%E5%8F%8C%E8%BE%B9%E6%9D%A1%E7%BA%A6%E4%B8%80%E8%A7%88%E8%A1%A8&fg=2",
                "es": "双边条约一览表", "clazz": "法律法规_国际条约_其他"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=6&sortName=%E5%A4%9A%E8%BE%B9%E6%9D%A1%E7%BA%A6%E4%B8%80%E8%A7%88%E8%A1%A8&fg=2",
                "es": "多边条约一览表", "clazz": "法律法规_国际条约_其他"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=7&sortName=%E8%B0%85%E8%A7%A3%E5%A4%87%E5%BF%98%E5%BD%95&fg=2",
                "es": "谅解备忘录", "clazz": "法律法规_国际条约_谅解备忘录"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=8&sortName=%E5%AE%A3%E8%A8%80/%E5%A3%B0%E6%98%8E&fg=2",
                "es": "宣言_声明", "clazz": "法律法规_国际条约_宣言_声明"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=9&sortName=%E8%81%94%E5%90%88%E5%85%AC%E6%8A%A5&fg=2",
                "es": "联合公报", "clazz": "法律法规_国际条约_联合公报"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=10&sortName=%E6%9D%A1%E7%BA%A6&fg=2",
                "es": "条约", "clazz": "法律法规_国际条约_条约"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=11&sortName=%E6%8D%A2%E6%96%87&fg=2",
                "es": "换文", "clazz": "法律法规_国际条约_换文"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=12&sortName=%E6%96%87%E4%BB%B6&fg=2",
                "es": "文件", "clazz": "法律法规_国际条约_文件"},
            {
                "url": "http://policy.mofcom.gov.cn/pact/index.shtml?sortId=4&sortName=%E5%85%B6%E4%BB%96&fg=2",
                "es": "其他", "clazz": "法律法规_国际条约_其他"}
        ]
        # 获取最小级分类号
        self.year_url = 'http://policy.mofcom.gov.cn/pact/index.shtml?pactTp={}&sortId={}&sortName={}&fg={}'
        self.cookie_dict = ''
        self.cookie_str = ''
        self.num = 0

    def __getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(10):
            resp = self.download_middleware.getResp(url=url,
                                                    mode=mode,
                                                    s=s,
                                                    data=data,
                                                    cookies=cookies,
                                                    referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 200:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            return None

    def getCategory(self):
        # 遍历入口页列表
        for index in self.index_list:
            index_url = index['url']
            es = index['es']
            clazz = index['clazz']
            id = self.server.getId(index_url)
            index_resp = self.__getResp(url=index_url, mode='GET')
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
            year_list = self.server.getYearList(resp=index_text, id=id, year_url=self.year_url, es=es, clazz=clazz, para='签订时间')
            # 列表页进入队列
            self.dao.QueueJobTask(key=config.REDIS_SHANGWUBU_TIAOYUE, data=year_list)
            # print(year_list)
            # print(len(year_list))

    def getProfile(self, first_text, task, nianfen, es, clazz):
        # 判断总页数
        total_num = self.server.totalPages(resp=first_text)
        # print(total_num)
        # 如果有，请求下一页，获得响应
        if int(total_num) > 1:
            for i in range(2, int(total_num) + 1):
                next_url = task['url'] + '&pageNum=' + str(i)
                # 获取下一页响应
                next_resp = self.__getResp(url=next_url, mode='GET')

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
                    self.dao.saveTaskToMysql(table=config.MYSQL_LAW, memo=url, ws='中华人民共和国商务部', es='中外条约')
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
        first_resp = self.__getResp(url=url, mode='GET')
        if not first_resp:
            LOGGING.error('列表首页响应失败, url: {}'.format(url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_SHANGWUBU_TIAOYUE, data=task)
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
            self.dao.saveTaskToMysql(table=config.MYSQL_LAW, memo=url, ws='中华人民共和国商务部', es='中外条约')
        # 获取详情url
        self.getProfile(first_text=first_text, task=task, nianfen=nianfen, es=es, clazz=clazz)

    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_SHANGWUBU_TIAOYUE,
                                             count=10,
                                             lockname=config.REDIS_SHANGWUBU_TIAOYUE_LOCK)
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
