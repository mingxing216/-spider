# -*-coding:utf-8-*-
'''
专利说明书文本抓取爬虫
'''

import os
import sys
import time
import json
from pymongo import MongoClient

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Project.DaWeiSpiderProject.middleware import download_middleware
from Project.DaWeiSpiderProject.dao import dao
from Project.DaWeiSpiderProject.services import services
from Utils import redispool_utils
from Utils import create_ua_utils

log_file_dir = 'DaWeiSpiderProject'  # LOG日志存放路径
LOGNAME = '<大为专利数据抓取>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.dao = dao.Dao(logging=LOGGING)
        self.server = services.ApiServeice(logging=LOGGING)
        self.download = download_middleware.Download_Middleware(logging=LOGGING)
        self.patent_mobile_list = []
        self.patent_mobile_index = 0

    def createMongoClient(self):
        mongo_client = MongoClient(host=settings.M_HOST, port=settings.M_PORT)
        client = mongo_client['spider']['ss_patent_data']

        return client

    # 从redis获取账号池内账号
    def getPatentMobileList(self, redis_client, key):
        mobile_list = self.dao.getPatentMobileForRedis(redis_client=redis_client, key=key)
        for mobile in mobile_list:
            self.patent_mobile_list.append(mobile)

    # 提取数据
    def handle(self, resp, url, ua):
        return_data = {}
        resp_dict = json.loads(resp)
        try:
            ErrorInfo = resp_dict['ErrorInfo']
            if ErrorInfo == 'no patent found.':

                return None
        except:
            # 获取说明书
            return_data['shuoMingShu'] = self.server.getShuoMingShu(resp=resp_dict)

            return return_data

    def run(self, mobile_pool_key):
        redis_client = redispool_utils.createRedisPool() # redis对象
        mongo_client = self.createMongoClient() # mongo对象
        # 从redis获取账号池内账号
        self.getPatentMobileList(redis_client=redis_client, key=mobile_pool_key)
        while True:
            if not self.patent_mobile_list:
                LOGGING.error('账号队列内无账号')
                # 从redis获取账号池内账号
                self.getPatentMobileList(redis_client=redis_client, key=mobile_pool_key)
                time.sleep(10)
                continue
            ua = create_ua_utils.get_ua()  # User_Agent
            proxy = self.server.getProxy()  # 代理IP
            LOGGING.info('当前ua: {}'.format(ua))
            LOGGING.info('当前代理: {}'.format(proxy))
            for user in self.patent_mobile_list[self.patent_mobile_index:]:
                # 获取当前账号在列表中的索引
                user_index = self.patent_mobile_list.index(user)
                # 设置全局索引
                self.patent_mobile_index = user_index
                # 获取大为账号参数响应
                user_guid_resp = self.download.getUserGuid_resp(user=user, proxy=proxy, ua=ua)
                if user_guid_resp is None:
                    LOGGING.error('获取大为账号GUID响应失败')
                    break

                # 获取大为账号GUID
                user_guid = self.server.getUserGuid(resp=user_guid_resp)  # 大为账号GUID
                if user_guid is None:
                    LOGGING.error('提取大为账号GUID失败')
                    continue

                # # 获取任务url
                patent_url = self.dao.getInnojoyPatentUrl(redis_client=redis_client)
                # patent_url = 'http://www.innojoy.com/patent/patent.html?docno=CN201810359894.1&trsdb=fmzl&showList=true'

                # 获取专利号
                patent_number = self.server.getPatentNumber(resp=patent_url)
                if patent_number is None:
                    LOGGING.error('任务专利号获取失败')
                    continue

                # 获取地区分类号
                patent_region_number = self.server.getPatentRegionNumber(resp=patent_url)
                if patent_region_number is None:
                    LOGGING.error('任务专利地区分类号获取失败')
                    continue

                # 获取专利详情接口响应
                API_resp = self.download.getPatentApiResp(patent_url=patent_url,
                                                          userID=user_guid,
                                                          database=patent_region_number,
                                                          query=patent_number,
                                                          ua=ua,
                                                          proxy=proxy)

                if API_resp is None:
                    # 任务扔回redis任务队列
                    self.dao.saveInnojoyPatentUrlForRedis(redis_client=redis_client, url=patent_url)
                    break
                API_resp_dect = json.loads(API_resp)
                ReturnValue = API_resp_dect['ReturnValue']
                if ReturnValue != 0:
                    value = API_resp_dect['ErrorInfo']
                    if value == 'verification':
                        LOGGING.error('出现验证码')
                        # 删除账号
                        self.patent_mobile_list.remove(user)
                        self.server.delInnojoyMobile(redis_client=redis_client, key=mobile_pool_key, value=user)
                        # 任务扔回队列
                        self.dao.saveInnojoyPatentUrlForRedis(redis_client=redis_client, url=patent_url)
                        break

                # 提取数据
                datas = self.handle(resp=API_resp, url=patent_url, ua=ua)

                if datas is None:
                    # 任务扔回队列
                    self.dao.saveInnojoyPatentUrlForRedis(redis_client=redis_client, url=patent_url)
                    continue

                # 存储数据
                self.dao.savePatentData(mongo_client=mongo_client, datas=datas)

                # 获取当前账号列表内有多少账号
                user_num = len(self.patent_mobile_list)
                # 如果全局索引达到当前账号队列最后位置， 将索引设置为0
                if self.patent_mobile_index + 1 == user_num:
                    self.patent_mobile_index = 0
                    break


if __name__ == '__main__':
    mobile_pool_key = sys.argv[1]
    s_main = SpiderMain()
    s_main.run(mobile_pool_key=mobile_pool_key)
    # po = ThreadPool(1)
    # for i in range(1):
    #     po.apply_async(func=s_main.run, args=(mobile_pool_key, ))
    # po.close()
    # po.join()
    # p1 = Process(target=s_main.run)
    # p2 = Process(target=s_main.run)
    # p3 = Process(target=s_main.run)
    # p4 = Process(target=s_main.run)
    # p1.start()
    # # p2.start()
    # # p3.start()
    # # p4.start()
    # p1.join()
    # # p2.join()
    # # p3.join()
    # # p4.join()
