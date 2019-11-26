# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangHaiWaiZhuanLi.middleware import download_middleware
from Project.ZhiWangHaiWaiZhuanLi.service import service
from Project.ZhiWangHaiWaiZhuanLi.dao import dao
from Project.ZhiWangHaiWaiZhuanLi import config

log_file_dir = 'ZhiWangHaiWaiZhuanLi'  # LOG日志存放路径
LOGNAME = '<知网_海外专利_task>'  # LOG名
NAME = '知网_海外专利_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
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
        self.country_number = 14  # 国家数
        # 入口页url
        self.index_url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD'
        # 指定年的主页url
        self.getYearIndexUrl = 'http://kns.cnki.net/kns/brief/brief.aspx?action=5&dbPrefix=SOPD&PageName=ASP.brief_result_aspx&Param=%E5%B9%B4%20=%20%27{}%27&recordsperpage=50'
        self.cookie_dict = ''
        self.cookie_str = ''
        self.number = 0

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 20:
                    LOGGING.info('出现验证码')
                    return 1

                else:
                    return response

            if resp['status'] == 1:
                return None

    def getUrlList(self, resp, category, country, year):
        return_data = []
        next_resp = resp
        page = 1
        while 1:
            # 获取url列表
            url_list = self.server.getUrlList(resp=next_resp)
            for url in url_list:
                return_data.append(url)

            # 获取下一页url
            next_url = self.server.getNextUrl(resp=next_resp)
            if not next_url:
                return return_data

            LOGGING.info('{}分类{}国家{}年第{}页：{}'.format(category, country, year, page + 1, next_url))

            while 1:
                # 下载下一页响应
                next_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=next_url,
                                           mode='GET',
                                           cookies=self.cookie_dict)
                # 处理验证码
                if next_resp == 1:
                    # 创建cookie
                    self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
                    self.download_middleware.getTimeListResp(category=category, country=country,
                                                             cookie=self.cookie_str)
                    # 获取指定年的专利列表首页响应
                    year_url = self.getYearIndexUrl.format(year)
                    year_index_resp = self.__getResp(func=self.download_middleware.getResp,
                                                     url=year_url,
                                                     mode='GET',
                                                     cookies=self.cookie_dict)
                    if year_index_resp is None:
                        continue

                    if year_index_resp == 1:
                        continue

                    year_index_response = year_index_resp.text
                    # 获取下一页url
                    next_page_url = self.server.getNextUrl(resp=year_index_response)
                    if next_page_url is None:
                        continue

                    # 替换页码获得新的下一页地址
                    next_url = self.server.replace_page_number(next_page_url, page + 1)

                    new_resp = self.__getResp(func=self.download_middleware.getResp,
                                              url=next_url,
                                              mode='GET',
                                              cookies=self.cookie_dict)

                    if new_resp is None:
                        continue
                    if new_resp == 1:
                        continue
                    next_resp = new_resp.text
                    page += 1
                    break
                else:
                    next_resp = next_resp.text
                    page += 1
                    break


    def start(self):
        category_number = []

        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET')
        if not index_resp:
            LOGGING.error('首页响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text

        # 获取第一分类列表
        first_list = self.server.getIndexClassList(resp=index_text)
        for first_url in first_list:
            first_resp = self.__getResp(func=self.download_middleware.getResp,
                                        url=first_url,
                                        mode='GET')
            if not first_resp:
                LOGGING.error('第一分类页获取失败, url: {}'.format(first_url))
                continue

            first_response = first_resp.text
            # 获取第二分类列表
            second_list = self.server.getSecondClassList(resp=first_response)
            for second_url in second_list:
                second_resp = self.__getResp(func=self.download_middleware.getResp,
                                             url=second_url,
                                             mode='GET')
                if not second_resp:
                    LOGGING.error('第二分类页获取失败, url: {}'.format(second_url))
                    continue
                second_response = second_resp.text
                # 获取第三分类号
                category_list = self.server.getCategoryNumber(resp=second_response)
                for category in category_list:
                    category_number.append(category)

        if not category_number:
            LOGGING.error('category_number is None')
            return

        # 遍历分类号
        for category in category_number:
            # 遍历国家
            for country in range(self.country_number):
                # 创建cookie
                self.cookie_dict, self.cookie_str = self.download_middleware.create_cookie()
                number = country + 1
                if number == 9:
                    number = '9+0'

                # 获取时间列表
                time_response = self.download_middleware.getTimeListResp(category=category, country=number,
                                                                         cookie=self.cookie_str)
                if time_response is None:
                    continue

                year_list = self.server.getYearList(resp=time_response)
                for year in year_list:
                    year_url = self.getYearIndexUrl.format(year)
                    # 获取指定年的专利列表首页响应
                    year_index_resp = self.__getResp(func=self.download_middleware.getResp,
                                                url=year_url,
                                                mode='GET',
                                                cookies=self.cookie_dict)
                    if year_index_resp is None:
                        continue

                    year_index_response = year_index_resp.text
                    # 获取专利主页url
                    url_list = self.getUrlList(year_index_response, category=category, country=number, year=year)
                    # 保存url
                    for url in url_list:
                        self.number += 1
                        LOGGING.info('当前已抓种子数量: {}'.format(self.number))
                        LOGGING.info('已存储种子: {}'.format(url))
                        self.dao.saveUrlToMysql(table=config.MYSQL_TASK, url=url)


                    # break
                # break
            # break



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
