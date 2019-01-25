# -*-coding:utf-8-*-

'''

'''
import sys
import os

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


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.country_number = 14    # 国家数
        self.index_url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD'

    def getUrlList(self, resp):
        return_data = []
        next_resp = resp
        while 1:
            # 获取url列表
            url_list = self.server.getUrlList(resp=next_resp)
            for url in url_list:
                return_data.append(url)

            # 获取下一页url
            next_url = self.server.getNextUrl(resp=next_resp)
            if next_url:
                # 下载下一页响应
                next_resp = self.download_middleware.getNextHtml(url=next_url)
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
                    # break

                # break
            # break

        # 遍历分类号
        for category in category_number:

            # 遍历国家
            for country in range(self.country_number):
                number = country + 1

                # 获取时间列表
                time_resp = self.download_middleware.getTimeListResp(category=category, country=number)
                year_list = self.server.getYearList(resp=time_resp)
                if year_list:
                    for year in year_list:
                        # 获取指定年的专利列表首页响应
                        index_html = self.download_middleware.getIndexHtml(year=year)
                        # 获取专利主页url，内置翻页功能
                        url_list = self.getUrlList(index_html)
                        # 保存url
                        for url in url_list:
                            LOGGING.info(url)
                            self.dao.saveUrlToMysql(url=url)


                        # break


                # break


if __name__ == '__main__':
    main = SpiderMain()
    main.start()
