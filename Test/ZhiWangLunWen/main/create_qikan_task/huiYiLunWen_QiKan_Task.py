# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import timeutils
from Test.ZhiWangLunWen.middleware import download_middleware
from Test.ZhiWangLunWen.service import service
from Test.ZhiWangLunWen.dao import dao
from Test.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_会议论文期刊_task>'  # LOG名
NAME = '知网_会议论文期刊_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化导航栏url
        self.daoHangUrl = 'http://navi.cnki.net/knavi/Common/LeftNavi/DPaper1'
        # 初始化论文集列表页url
        self.lunWenJiUrl = 'http://navi.cnki.net/knavi/Common/Search/DPaper1'

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    # 获取学科导航的最底层导航列表
    def getNavigationList(self, data):
        # 获取导航栏响应
        resp = self.__getResp(func=self.download_middleware.getResp, url=self.daoHangUrl, mode='POST', data=data)
        if not resp:
            LOGGING.error('导航栏响应获取失败。')
            return []

        response = resp.content.decode('utf-8')
        # 获取学科导航的最底层导航列表
        navigation_list = self.server.getNavigationList(resp=response)
        if not navigation_list:
            LOGGING.error('学科导航的最底层导航列表获取失败')
            return []

        return navigation_list

    # 获取论文集列表
    def handle(self, data):
        request_data = data
        return_data = []
        # 获取论文集列表首页响应
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.lunWenJiUrl,
                                    mode='POST',
                                    data=request_data)
        if not index_resp:
            LOGGING.error('论文集列表首页响应获取失败')
            return return_data

        index_response = index_resp.text
        # 获取文集数量
        huiYiWenJi_Number = self.server.getHuiYiWenJiNumber(resp=index_response)
        if not huiYiWenJi_Number:
            LOGGING.error('文集数量获取失败')
            return return_data

        # 生成文集总页数
        page_number = self.server.getWenJiPageNumber(huiYiWenJi_Number)
        for current_page in range(1, page_number + 1):
            request_data['pageindex'] = current_page
            page_resp = self.__getResp(func=self.download_middleware.getResp,
                                       url=self.lunWenJiUrl,
                                       mode='POST',
                                       data=request_data)
            if not page_resp:
                continue

            page_response = page_resp.text
            # 获取会议文集种子
            wenji_url_list = self.server.getWenJiUrlList(resp=page_response)
            for wenji_url in wenji_url_list:
                return_data.append(wenji_url)

        return return_data

    def start(self):
        # 生成导航栏页面post请求参数
        daohang_post_data = {
            "productcode": "CIPD",
            "index": "1",
            "random": "0.8249670375543876"
        }
        # 获取学科导航的最底层导航列表
        navigation_list = self.getNavigationList(daohang_post_data)
        for navigation in navigation_list:
            # 生成论文集列表首页请求参数
            lunWenJi_UrlData = self.server.getLunWenJiUrlData(data=navigation, page=1)
            # 获取论文集url列表
            url_list = self.handle(lunWenJi_UrlData)
            for url_data in url_list:
                table = config.QIKAN_URL_TABLE
                data_type = 'huiyi'
                create_at = timeutils.getNowDatetime()
                # 保存论文集url到mysql
                self.dao.saveLunWenJiUrl(table=table, url_data=url_data, data_type=data_type, create_at=create_at)


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
