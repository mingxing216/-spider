# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import random

import requests
from multiprocessing.pool import Pool, ThreadPool

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊_task'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_QiKan(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)
        self.s = requests.Session()
        # self.captcha_processor = CaptchaProcessor(self.server, self.download, self.s, logger)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        self.left_navi_url = 'https://navi.cnki.net/knavi/Common/LeftNavi/Journal?productcode=CJFD&index=1&random={}'
        self.search_url = 'https://navi.cnki.net/knavi/Common/Search/Journal'
        # 分类列表url
        self.fenlei_list_url = 'https://navi.cnki.net/knavi/Common/ClickNavi/Journal?'
        # 期刊列表页url
        self.qikan_list_url = 'https://navi.cnki.net/knavi/Common/Search/Journal'
        # 记录抓取种子数
        self.num = 0

    def _get_resp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download.get_resp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    logger.error('captcha | 出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def spider(self, SearchStateJson, page_number):
        for page in range(page_number):
            logger.info('第{}页'.format(page + 1))
            # 期刊列表页的请求data
            data = self.server.get_qi_kan_lie_biao_page_data(SearchStateJson=SearchStateJson, page=page + 1)
            # 期刊列表页的响应
            qikan_profile_resp = self._get_resp(url=self.qikan_list_url,
                                                method='POST',
                                                data=data)
            if not qikan_profile_resp:
                logger.error('catalog | 期刊列表页第 {} 页获取失败。data: {}'.format(page + 1, data['data']))
                yield None

            qikan_profile_text = qikan_profile_resp.text
            yield qikan_profile_text

    def all_magazine(self):
        # 生成左导航分类列表页url
        navi_url = self.left_navi_url.format(random.random())
        # 获取分类页源码
        navi_resp = self._get_resp(url=navi_url, method='GET')

        if not navi_resp:
            logger.error('classify | 分类页源码获取失败， url: {}'.format(navi_url))
            return

        form_data = {
            'SearchStateJson': '{"StateID":"","Platfrom":"","QueryTime":"","Account":"knavi",'
                               '"ClientToken":"","Language":"","CNode":{"PCode":"CJFD","SMode":"","OperateT":""},'
                               '"QNode":{"SelectT":"","Select_Fields":"","S_DBCodes":"","QGroup":[],'
                               '"OrderBy":"OTA|DESC","GroupBy":"","Additon":""}}',
            'displaymode': 1,
            'pageindex': 1,
            'pagecount': 21,
            'index': 1,
            'random': random.random()}
        # 获取期刊列表首页响应
        catalog_resp = self._get_resp(url=self.search_url,
                                         method='POST',
                                         data=form_data)
        if not catalog_resp:
            logger.error('catalog | 期刊列表首页响应失败， url: {}'.format(self.search_url))
            return

        # with open('catalog.html', 'w', encoding='utf-8') as f:
        #     f.write(catalog_resp.text)

        catalog_resp_text = catalog_resp.text
        # 获取总页数
        page_number = self.server.get_page_number(text=catalog_resp_text)
        # print(page_number)
        # 获取期刊列表页响应
        for text in self.spider(SearchStateJson=form_data.get('SearchStateJson'), page_number=page_number):
            # 获取期刊列表
            for task in self.server.get_qi_kan_list(text=text):
                # 保存数据
                # print(task)
                self.num += 1
                logger.info('profile | 已抓种子数量: {}'.format(self.num))
                self.dao.save_task_to_mysql(table=config.MYSQL_MAGAZINE, memo=task, ws='中国知网', es='期刊')

    def start(self):
        # 生成分类列表页url
        for fenlei_url in self.server.get_fen_lei_url(self.fenlei_list_url):
            # print(fenlei_url)
            # 获取分类页源码
            fenlei_resp = self._get_resp(url=fenlei_url, method='GET')

            # with open('fenlei.html', 'w', encoding='utf-8') as f:
            #     f.write(fenlei_resp.text)

            if not fenlei_resp:
                logger.error('classify | 分类页源码获取失败， url: {}'.format(fenlei_url))
                continue

            fenlei_text = fenlei_resp.text
            # 获取分类数据
            for fenlei_data in self.server.get_fen_lei_data(text=fenlei_text, page=1):
                # print(fenlei_data)
                # 分类名
                xueKeLeiBie = fenlei_data.get('xueKeLeiBie', "")
                heXinQiKan = fenlei_data.get('heXinQiKan', "")
                SearchStateJson = fenlei_data.get('SearchStateJson', "")
                # 获取期刊列表首页响应
                qikan_list_resp = self._get_resp(url=self.qikan_list_url,
                                                 method='POST',
                                                 data=fenlei_data['data'])
                if not fenlei_resp:
                    logger.error('catalog | 期刊列表首页响应失败， url: {}'.format(fenlei_url))
                    continue

                # with open('first.html', 'w', encoding='utf-8') as f:
                #     f.write(qikan_list_resp.text)

                qikan_first_text = qikan_list_resp.text
                # 获取总页数
                page_number = self.server.get_page_number(text=qikan_first_text)
                # print(page_number)
                # 获取期刊列表页响应
                for text in self.spider(SearchStateJson=SearchStateJson, page_number=page_number):
                    # 获取期刊列表
                    for task in self.server.get_qi_kan_list(text=text):
                        # 保存数据
                        task['s_xueKeLeiBie'] = xueKeLeiBie
                        task['s_zhongWenHeXinQiKanMuLu'] = heXinQiKan
                        print(task)
                        self.num += 1
                        logger.info('profile | 已抓种子数量: {}'.format(self.num))

                        self.dao.save_task_to_mysql(table=config.MYSQL_MAGAZINE, memo=task, ws='中国知网', es='期刊')


def process_start():
    main = SpiderMain()
    try:
        main.all_magazine()
        # main.start()
    except:
        logger.error(str(traceback.format_exc()))


if __name__ == '__main__':
    logger.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('======Time consuming is %.3fs======' % (end_time - begin_time))
