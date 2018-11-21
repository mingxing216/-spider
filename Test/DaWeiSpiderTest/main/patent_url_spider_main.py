# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import json
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
from Utils import create_ua_utils
from Test.DaWeiSpiderTest.services import services
from Test.DaWeiSpiderTest.middleware import download_middleware
from Test.DaWeiSpiderTest.dao import dao

log_file_dir = 'DaWeiSpiderTest'  # LOG日志存放路径
LOGNAME = '<大为专利种子抓取>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.index_url = 'http://www.innojoy.com/client/interface.aspx' # post请求url
        self.server = services.ApiServeice(logging=LOGGING)
        self.download = download_middleware.Download_Middleware(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)
        self.sic_number = 0 # 当前专利分类索引
        self.region_number = 0 # 当前专利地区分类索引
        self.page = 1 # 当前在抓页数
        self.page_count = 0 # 总页数
        self.page_guid = "" # 下一页页码guid
        self.error = ''


    def run(self):
        redis_cli = redispool_utils.createRedisPool() # redis连接池
        mysql_cli = mysqlpool_utils.createMysqlPool() # mysql连接池

        while 1:
            # 初始化当前专利分类索引
            self.sic_number = self.dao.getInnojoySicNumber(redis_client=redis_cli)
            # 初始化当前专利地区分类索引
            self.region_number = self.dao.getInnojoyRegionNumber(redis_client=redis_cli)
            # 初始化当前在抓页数
            self.page = self.dao.getInnojoyPage(redis_client=redis_cli)
            # 初始化下一页页码guid
            self.page_guid = self.dao.getInnojoyPageGuid(redis_client=redis_cli)
            self.error = '' # 初始化错误
            # 获取innojoy账号
            user = self.server.getInnojoyMobileToUrlSpider(redis_client=redis_cli)
            # user = '15246143021'
            if user is None:
                LOGGING.info('redis队列无innojoy账号')
                time.sleep(10)
                continue
            ua = create_ua_utils.get_ua() # User_Agent
            proxy = self.server.getProxy() # 代理IP
            LOGGING.info('当前ua: {}'.format(ua))
            LOGGING.info('当前代理: {}'.format(proxy))

            # 获取大为账号参数响应
            user_guid_resp = self.download.getUserGuid_resp(user=user, proxy=proxy, ua=ua)
            if user_guid_resp is None:
                LOGGING.error('获取大为账号GUID响应失败')
                # 将innojoy账号扔回redis
                self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)
                continue
            user_guid = self.server.getUserGuid(resp=user_guid_resp) # 大为账号GUID
            if user_guid is None:
                LOGGING.error('提取大为账号GUID失败')
                # 将innojoy账号扔回redis
                self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)

            # 获取专利分类接口响应
            patent_type_resp = self.download.getPatentType_resp(guid=user_guid, proxy=proxy, ua=ua)
            if patent_type_resp is None:
                LOGGING.error('获取专利分类接口响应失败')
                continue
            sic_list = self.server.getSicList(resp=patent_type_resp) # 专利分类ID列表
            if sic_list is None:
                LOGGING.error('提取专利分类失败')
                # 将innojoy账号扔回redis
                self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)


            # 获取地区分类接口响应
            region_resp = self.download.getRegion_resp(proxy=proxy, ua=ua)
            if region_resp is None:
                LOGGING.error('获取地区分类接口响应失败')
                continue
            region_list = self.server.getRgionList(resp=region_resp)
            if region_list is None:
                LOGGING.error('提取地区分类参数失败')
                # 将innojoy账号扔回redis
                self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)

            for sic in sic_list:
                if sic_list.index(sic) != self.sic_number:
                    continue
                for region in region_list:
                    LOGGING.info(str(region_list.index(region)) + str('/') + str(len(region_list)))
                    if region_list.index(region) != self.region_number:
                        continue

                    # 获取第一页响应
                    one_page_resp = self.download.getPageResp(sic=sic, region=region, page=1, proxy=proxy, ua=ua,
                                                              guid=user_guid, page_guid='')
                    LOGGING.info('首页响应：' + '\n' + str(one_page_resp) + '\n')
                    if one_page_resp is None:
                        self.error = 1
                        # 将innojoy账号扔回redis
                        self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)
                        break
                    one_page_resp_dict = json.loads(one_page_resp)
                    one_ReturnValue = one_page_resp_dict['ReturnValue']
                    if one_ReturnValue != 0:
                        value = one_page_resp_dict['ErrorInfo']
                        if value == 'verification':
                            self.error = value
                            break
                        LOGGING.error(value)
                        self.error = value
                        break
                    else:
                        self.error = ''

                    # 获取下一页GUID
                    self.page_guid = self.server.getPageGuid(resp=one_page_resp)
                    # 同步下一页guid到redis数据库
                    self.dao.setInnojoyPageGuid(redis_client=redis_cli, value=self.page_guid)

                    for ii in range(8):
                        LOGGING.info('当前正在抓取第{}个专利分类下的{}地区分类的第{}页'.format(self.sic_number + 1, self.region_number + 1, self.page))
                        # 获取当前页响应
                        page_resp = self.download.getPageResp(sic=sic, region=region, page=self.page, proxy=proxy, ua=ua,  guid=user_guid, page_guid=self.page_guid)
                        LOGGING.info('当前页响应：' + '\n' + str(page_resp) + '\n')
                        if page_resp is None:
                            self.error = 1
                            # 将innojoy账号扔回redis
                            self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)
                            break
                        # 获取响应状态
                        page_resp_dict = json.loads(page_resp)
                        ReturnValue = page_resp_dict['ReturnValue']
                        if ReturnValue != 0:
                            value = page_resp_dict['ErrorInfo']
                            if value == 'verification':
                                # 将innojoy账号扔回redis
                                self.dao.saveInnojoyMobile_redis(redis_client=redis_cli, value=user)
                                self.error = value
                                break
                            LOGGING.error(value)
                            self.error = value
                            break
                        else:
                            self.error = ''

                        # 获取下一页GUID
                        self.page_guid = self.server.getPageGuid(resp=page_resp)
                        # 同步下一页guid到redis数据库
                        self.dao.setInnojoyPageGuid(redis_client=redis_cli, value=self.page_guid)
                        # 获取当前页专利url列表
                        count, patent_url_list = self.server.getPatentUrlList(resp=page_resp)
                        # 计算总页数
                        self.page_count = self.server.getPageCount(count=count)
                        for patent_url in patent_url_list:
                            # 存储专利种子到mysql
                            self.dao.saveInnojoyPatentUrl(mysql_client=mysql_cli, url=patent_url)

                        LOGGING.info('已抓取第{}页'.format(self.page))

                        # 生成下一页
                        self.page += 1
                        # 同步当前页数到redis
                        self.dao.setInnojoyPage(redis_client=redis_cli, value=self.page)
                        # 判断当前是否是最后一页
                        if self.page > self.page_count:
                            self.page = 1 # 初始化页数
                            # 同步当前页数到redis
                            self.dao.setInnojoyPage(redis_client=redis_cli, value=self.page)
                            break

                        time.sleep(5)
                        # break
                    LOGGING.info('结束翻页')
                    if self.error != '':
                        break
                    else:
                        # 判断当前是否是最后一页
                        if self.page > self.page_count:
                            self.region_number += 1
                            # 同步当前专利地区分类索引到redis
                            self.dao.setInnojoyRegionNumber(redis_client=redis_cli, value=self.region_number)
                        else:
                            break

                    # break

                if self.error != '':
                    break
                else:
                    # 判断当前分类是否已达到最后一个分类
                    if self.region_number > len(region_list):
                        self.sic_number += 1
                        # 同步当前专利分类索引到redis
                        self.dao.setInnojoySicNumber(redis_client=redis_cli, value=self.sic_number)
                    else:
                        break

                # break

            # break


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
