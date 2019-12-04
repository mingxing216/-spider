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
from Project.ZhiWang.middleware import download_middleware
from Project.ZhiWang.service import service
from Project.ZhiWang.dao import dao
from Project.ZhiWang import config

log_file_dir = 'ZhiWang'  # LOG日志存放路径
LOGNAME = '<知网_发明公开_task>'  # LOG名
NAME = '知网_发明公开_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.GongKaiDownloader(logging=LOGGING,
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
        self.index_url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SCPD_FM'
        # 指定年的主页url
        self.getYearIndexUrl = 'http://kns.cnki.net/kns/brief/brief.aspx?action=5&dbPrefix=SCPD_FM&PageName=ASP.brief_result_aspx&Param=%e5%b9%b4+%3d+%27{}%27&isinEn=0&RecordsPerPage=50'
        # 获取最小级分类号
        self.category_number = []
        self.cookie_dict = ''
        self.cookie_str = ''
        self.num = 0

    def __getResp(self, func, url, mode, s=None, data=None, cookies=None, referer=None):
        while 1:
            resp = func(url=url, mode=mode, s=s, data=data, cookies=cookies, referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.error('出现验证码')
                    # continue
                    return response

                else:
                    return response

            if resp['code'] == 1:
                return None

    def getCategory(self):
        # 访问入口页
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('入口页面响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text
        # with open ('index.html', 'w') as f:
        #     f.write(index_text)

        # 获取第一层分类列表
        first_list = self.server.getIndexClassList(resp=index_text)
        # print(first_list)
        if first_list:
            for first_url in first_list:
                first_resp = self.__getResp(func=self.download_middleware.getResp,
                                            url=first_url,
                                            mode='GET')
                if not first_resp:
                    LOGGING.error('第一分类页获取失败, url: {}'.format(first_url))
                    first_list.append(first_url)
                    continue

                first_response = first_resp.text
                # 获取第二层分类列表
                second_list = self.server.getSecondClassList(resp=first_response)
                # print(second_list)
                if second_list:
                    for second_url in second_list:
                        second_resp = self.__getResp(func=self.download_middleware.getResp,
                                                     url=second_url,
                                                     mode='GET')
                        if not second_resp:
                            LOGGING.error('第二分类页获取失败, url: {}'.format(second_url))
                            second_list.append(second_url)
                            continue
                        second_response = second_resp.text
                        # 获取第三层分类号
                        category_list = self.server.getCategoryNumber(resp=second_response)
                        # print(category_list)
                        # 进入队列
                        self.dao.QueueJobTask(key=config.REDIS_FM_CATEGORY, data=category_list)
                        if category_list:
                            for category in category_list:
                                self.category_number.append(category)

        print(self.category_number)
        print(len(self.category_number))

    def getProfile(self, resp, category, year):
        next_resp = resp
        next_num = 2

        while True:
            # 响应成功，提取详情页种子
            next_text = next_resp.text
            next_urls = self.server.getDetailUrl(resp=next_text)
            # print(next_urls)
            for url in next_urls:
                # 保存url
                self.num += 1
                LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                # 存入数据库
                self.dao.saveTaskToMysql(table=config.MYSQL_PATENT, memo=url, ws='中国知网', es='发明公开专利')

            # 判断是否有下一页
            next_url = self.server.hasNextUrl(resp=next_text)
            # print(next_url)
            # 如果有，请求下一页，获得响应
            if next_url:
                while True:
                    # 获取下一页响应
                    next_resp = self.__getResp(func=self.download_middleware.getResp,
                                               url=next_url,
                                               mode='GET',
                                               cookies=self.cookie_dict)

                    # 如果响应获取失败，重新访问，并记录这一页种子
                    if not next_resp:
                        LOGGING.error('{}分类下{}年第{}页响应获取失败, url: {}'.format(category, year, next_num, next_url))
                        continue

                    # 处理验证码
                    if '请输入验证码' in next_resp.text or '对不起，服务器上不存在此用户' in next_resp.text:
                        LOGGING.error('翻到{}分类下{}年第{}页时cookie失效, 重新创建cookie, url: {}'.format(category, year, next_num, next_url))
                        # 创建cookie
                        self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
                        self.download_middleware.getTimeListResp(referer=self.index_url,
                                                                 category=category,
                                                                 cookie=self.cookie_str)
                        # 获取指定年的专利列表首页响应
                        year_url = self.getYearIndexUrl.format(year)
                        year_first_resp = self.__getResp(func=self.download_middleware.getResp,
                                                         url=year_url,
                                                         mode='GET',
                                                         cookies=self.cookie_dict)
                        if not year_first_resp:
                            LOGGING.error('{}分类下{}年的列表首页响应获取失败, url: {}'.format(category, year, year_url))
                            continue
                        else:
                            LOGGING.info('{}分类下{}年的列表首页响应成功'.format(category, year))
                            continue

                    else:
                        break

                # 响应成功，添加log日志
                LOGGING.info('已翻到{}分类下{}年第{}页'.format(category, year, next_num))

                next_num += 1

            else:
                LOGGING.info('已翻到{}分类下{}年最后一页'.format(category, year))
                break


    def run(self, category):
        year_index = 0
        while True:
            # 创建cookie
            self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
            # 获取时间列表
            time_response = self.download_middleware.getTimeListResp(referer=self.index_url,
                                                                     category=category,
                                                                     cookie=self.cookie_str)
            if time_response is None:
                return
            # 获年份列表
            year_list = self.server.getYearList(resp=time_response)
            # print(year_list)
            try:
                # 获取某一年
                year = year_list[year_index]
                LOGGING.info('已进入{}分类下{}年'.format(category, year))
                # 获取指定年的列表页首页url
                year_url = self.getYearIndexUrl.format(year)
                # print(year_url)

                while True:
                    # 获取列表首页响应
                    year_first_resp = self.__getResp(func=self.download_middleware.getResp,
                                                     url=year_url,
                                                     mode='GET',
                                                     cookies=self.cookie_dict)
                    if not year_first_resp:
                        LOGGING.error('{}分类下{}年的列表首页响应获取失败, url: {}'.format(category, year, year_url))
                        # 最小一级分类号存入列表
                        self.category_number.append(category)
                        return

                    # 处理验证码
                    if '请输入验证码' in year_first_resp.text or '对不起，服务器上不存在此用户' in year_first_resp.text:
                        LOGGING.error('访问{}分类下{}年的列表页首页时cookie失效, 重新创建cookie, url: {}'.format(category, year, year_url))
                        # 创建cookie
                        self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
                        self.download_middleware.getTimeListResp(referer=self.index_url,
                                                                 category=category,
                                                                 cookie=self.cookie_str)
                        continue

                    else:
                        LOGGING.info('{}分类下{}年的列表首页响应成功'.format(category, year))
                        break

                self.getProfile(resp=year_first_resp, category=category, year=year)

                year_index += 1

            except Exception:
                LOGGING.info('已翻完{}分类下最后一年的最后一页'.format(category))
                break


    def start(self):
        # if self.category_number:
        #     # 遍历分类号
        #     for category in self.category_number:
        #         self.run(category)
        #
        #     else:
        #         LOGGING.info('分类号已全部遍历完毕，结束程序')
        #         return
        #
        # else:
        #     LOGGING.info('category_number is None')
        #     return



        while 1:
            # 获取任务
            category_list = self.dao.getTask(key=config.REDIS_FM_CATEGORY,
                                         count=1,
                                         lockname=config.REDIS_FM_CATEGORY_LOCK)
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
        # main.getCategory()
        main.start()
        # main.run("A22C")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
