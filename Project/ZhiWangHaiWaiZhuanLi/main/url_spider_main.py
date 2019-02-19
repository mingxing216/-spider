# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangHaiWaiZhuanLi.middleware import download_middleware
from Project.ZhiWangHaiWaiZhuanLi.service import service
from Project.ZhiWangHaiWaiZhuanLi.dao import dao
from Project.ZhiWangHaiWaiZhuanLi import config

log_file_dir = 'ZhiWangHaiWaiZhuanLi'  # LOG日志存放路径
LOGNAME = '<知网海外专利任务爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.UrlDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.UrlServer(logging=LOGGING)
        self.dao = dao.UrlDao(logging=LOGGING)
        self.number = 0


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.country_number = 14    # 国家数
        self.index_url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD'
        self.cookie = ''

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
            LOGGING.info('{}分类{}国家{}年第{}页：{}'.format(category, country, year, page + 1, next_url))

            if next_url:
                # 下载下一页响应
                next_resp = self.download_middleware.getNextHtml(url=next_url, cookie=self.cookie)
                if next_resp is None:
                    # 生成新的cookie
                    self.cookie = self.download_middleware.create_cookie()
                    self.download_middleware.getTimeListResp(category=category, country=country, cookie=self.cookie)
                    # 获取首页响应
                    index_html = self.download_middleware.getIndexHtml(year=year, cookie=self.cookie)
                    # 获取下一页url
                    next_page_url = self.server.getNextUrl(resp=index_html)
                    # 替换页码获得新的下一页地址
                    next_url = self.server.replace_page_number(next_page_url, page+1)

                    next_resp = self.download_middleware.getNextHtml(url=next_url, cookie=self.cookie)
                page += 1
                continue

            else:
                break
            
        return return_data

    def start(self):
        category_number = []

        index_resp = self.download_middleware.getResp(url=self.index_url)
        resp = index_resp.content.decode('utf-8')
        # 获取第一分类列表
        first_list = self.server.getIndexClassList(resp=resp)
        for first_url in first_list:
            first_resp = self.download_middleware.getResp(url=first_url)
            # 获取第二分类列表
            second_list = self.server.getSecondClassList(resp=first_resp)
            for second_url in second_list:
                second_resp = self.download_middleware.getResp(url=second_url)
                # 获取第三分类号
                category_list = self.server.getCategoryNumber(resp=second_resp)
                for category in category_list:
                    category_number.append(category)

        # 遍历分类号
        for category in category_number:
            # 遍历国家
            for country in range(self.country_number):
                # 创建cookie
                self.cookie = self.download_middleware.create_cookie()
                number = country + 1
                if number == 9:
                    number = '9+0'

                # 获取时间列表
                time_resp = self.download_middleware.getTimeListResp(category=category, country=number, cookie=self.cookie)
                year_list = self.server.getYearList(resp=time_resp)
                for year in year_list:
                    # 获取指定年的专利列表首页响应
                    try:
                        index_html = self.download_middleware.getIndexHtml(year=year, cookie=self.cookie)
                    except Exception as e:
                        LOGGING.error(e)
                        continue
                    # 获取专利主页url，内置翻页功能
                    try:
                        url_list = self.getUrlList(index_html, category=category, country=number, year=year)
                    except Exception as e:
                        LOGGING.error(e)
                        continue

                    # 保存url
                    for url in url_list:
                        self.number += 1
                        LOGGING.info('当前已抓种子数量: {}'.format(self.number))
                        LOGGING.info('已存储种子: {}'.format(url))
                        self.dao.saveUrlToMysql(url=url)


if __name__ == '__main__':
    LOGGING.info('=========start object=========')
    begin_time = time.time()
    main = SpiderMain()
    main.start()
    LOGGING.info('=========end object=========')
    LOGGING.info('=========Time consuming {}s'.format(int(time.time() - begin_time)))

