# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
import time
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.QiChaCha.dao import dao
from Project.QiChaCha.services import services
from Project.QiChaCha.middleware import download_middleware
from Utils import redispool_utils
from Utils import mysqlpool_utils
from Utils import create_ua_utils

log_file_dir = 'QiChaCha'  # LOG日志存放路径
LOGNAME = '<企查查任务抓取>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

class SpiderMain(object):
    def __init__(self, cookie, user_agent):
        # 入口页url
        self.index_url = 'https://www.qichacha.com/'
        self.download = download_middleware.Download(cookies=cookie, user_agent=user_agent)
        self.server = services.Services_Logging()
        self.dao = dao.Dao()

    def run(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        while 1:
            # 获取入口页响应
            index_resp = self.download.getResp(logging=LOGGING, redis_client=redis_client, url=self.index_url)
            if not index_resp:
                LOGGING.error('入口页响应获取失败')
                continue

            LOGGING.info('入口页响应获取成功')
            print(index_resp)

            # # 获取地区分类url列表
            # add_url_list = self.server.getAddUrlList(logging=LOGGING, resp=index_resp)
            #
            # # 获取行业分类url列表
            # industry_url_list = self.server.getIndustryUrlList(logging=LOGGING, resp=index_resp)
            #
            # '''处理地区分类'''
            # # # 获取cookie
            # # cookie_list = self.dao.getCookieList(logging=LOGGING, redis_client=redis_client)
            # for add_url in add_url_list:
            #     # 限定最大翻页500页
            #     for i in range(500):
            #         url = re.sub(r"1\.html", "{}.html".format(i + 1), add_url)
            #         # 获取当前页响应
            #         page_resp = self.download.getResp(logging=LOGGING, redis_client=redis_client, url=url)
            #         # 获取企业url列表
            #         if page_resp is None:
            #             continue
            #         company_url_list = self.server.getCompanyUrlList(logging=LOGGING, resp=page_resp)
            #         # 判断是否到最后一页
            #         if not company_url_list:
            #             break
            #         # 保存企业url
            #         self.dao.saveCompanyUrl(logging=LOGGING, mysql_client=mysql_client, data=company_url_list)
            #
            #     time.sleep(random.randint(40, 60))
            #
            # '''处理行业分类'''
            # # for industry_url in industry_url_list:
            # #     # 限定最大翻页500页
            # #     for i in range(500):
            # #         url = re.sub(r"&p=\d+", "&p={}".format(i + 1), industry_url)
            # #         # 获取当前页响应
            # #         page_resp = self.download.getIndustryResp(logging=LOGGING, redis_client=redis_client, url=url)
            # #         if page_resp is None:
            # #             continue
            # #         # 获取企业url列表
            # #         company_url_list = self.server.getCompanyUrlList(logging=LOGGING, resp=page_resp)
            # #         # 判断是否到最后一页
            # #         if not company_url_list:
            # #             break
            # #         # 保存企业url
            # #         self.dao.saveCompanyUrl(logging=LOGGING, mysql_client=mysql_client, data=company_url_list)
            # #
            # #     time.sleep(random.randint(40, 60))
            break

if __name__ == '__main__':
    cookies = 'null'
    user_agent = create_ua_utils.get_ua()
    main = SpiderMain(cookie=cookies, user_agent=user_agent)
    main.run()
