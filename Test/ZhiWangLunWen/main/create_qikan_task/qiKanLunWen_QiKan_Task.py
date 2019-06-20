# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import hashlib
from multiprocessing import Pool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import timeutils
from Test.ZhiWangLunWen.middleware import download_middleware
from Test.ZhiWangLunWen.service import service
from Test.ZhiWangLunWen.dao import dao
from Test.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_期刊论文期刊_task>'  # LOG名
NAME = '知网_期刊论文期刊_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.QiKanLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.QiKanLunWen_QiKanTaskDao(logging=LOGGING,
                                                mysqlpool_number=config.MYSQL_POOL_NUMBER,
                                                redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 分类列表url
        self.fenlei_list_url = 'http://navi.cnki.net/knavi/Common/ClickNavi/Journal?'
        # 期刊列表页url
        self.qikan_list_url = 'http://navi.cnki.net/knavi/Common/Search/Journal'

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if len(response.text) < 200:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    def spider(self, SearchStateJson, page_number):
        for page in range(page_number):
            LOGGING.info('第{}页'.format(page + 1))
            # 期刊列表页的请求data
            data = self.server.getQiKanLieBiaoPageData(SearchStateJson=SearchStateJson, page=page + 1)
            # 期刊列表页的响应
            qikan_list_page_resp = self.__getResp(func=self.download_middleware.getResp,
                                                  url=self.qikan_list_url,
                                                  mode='POST',
                                                  data=data)
            if not qikan_list_page_resp:
                continue

            qikan_list_page_response = qikan_list_page_resp.text
            yield qikan_list_page_response

    def start(self):
        # 生成分类列表页url
        for fenlei_url in self.server.getFenLeiUrl(self.fenlei_list_url):
            # 获取分类页源码
            fenlei_resp = self.__getResp(func=self.download_middleware.getResp,
                                         url=fenlei_url,
                                         mode='GET')
            if not fenlei_resp:
                continue

            fenlei_response = fenlei_resp.text
            # 获取分类数据
            for fenlei_data in self.server.getFenLeiData(resp=fenlei_response, page=1):
                if not fenlei_data:
                    continue

                # 分类名
                column_name = fenlei_data['column_name']
                SearchStateJson = fenlei_data['SearchStateJson']

                # 获取期刊列表首页响应
                qikan_list_resp = self.__getResp(func=self.download_middleware.getResp,
                                                 url=self.qikan_list_url,
                                                 mode='POST',
                                                 data=fenlei_data['data'])
                if not qikan_list_resp:
                    continue

                qikan_list_response = qikan_list_resp.text
                # 获取总页数
                page_number = self.server.getPageNumber(resp=qikan_list_response)
                # 获取期刊列表页响应
                for resp in self.spider(SearchStateJson=SearchStateJson, page_number=page_number):
                    # 获取期刊列表
                    for title, url in self.server.getQiKanList(resp=resp):
                        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        data = {
                            'sha': sha,
                            'title': title,
                            'url': url,
                            'column_name': column_name
                        }
                        # 保存数据
                        self.dao.saveData(table=config.QIKAN_URL_TABLE, sha=sha, memo=data, create_at=timeutils.getNowDatetime())


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
