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
from Project.Jstor.middleware import download_middleware
from Project.Jstor.service import service
from Project.Jstor.dao import dao
from Project.Jstor import config

log_file_dir = 'Jstor'  # LOG日志存放路径
LOGNAME = '<JSTOR_期刊论文_task>'  # LOG名
NAME = 'JSTOR_期刊论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


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
        self.index_url = 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=&ed=&acc=dfr'
        self.cookie_dict = ''
        self.num = 0

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    def start(self):
        # 存放详情种子
        detail_urls = []
        # 获取cookie
        self.cookie_dict = self.download_middleware.create_cookie()
        # 请求页面，获取响应
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.index_url,
                                    mode='GET',
                                    cookies=self.cookie_dict)

        # with open('jstor.txt', 'w') as f:
        #     f.write(index_resp.text)

        if not index_resp:
            LOGGING.error('首页响应获取失败, url: {}'.format(self.index_url))
            return

        index_text = index_resp.text

        # 遍历所有学科，获取到学科名称及种子
        subject_url_list = self.server.getSubjectUrlList(index_text, index_url=self.index_url)
        print(subject_url_list)

        # 遍历所有各学科列表url,获取详情url
        for subject in subject_url_list:
            # first_url = subject['url']
            first_url = 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=&ed=&disc_developmentalcellbiology-discipline_facet=ZGV2ZWxvcG1lbnRhbGNlbGxiaW9sb2d5LWRpc2NpcGxpbmU%3D'

            # 请求页面，获取响应
            first_resp = self.__getResp(func=self.download_middleware.getResp,
                                        url=first_url,
                                        mode='GET',
                                        cookies=self.cookie_dict)
            # 获取首页详情url及传递学科名称
            if first_resp:
                first_urls = self.server.getDetailUrl(resp=first_resp.text, xueke=subject['xueKeLeiBie'])
                for url in first_urls:
                    # 保存url
                    self.num += 1
                    LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                    LOGGING.info('已存储种子: {}'.format(url))
                    self.dao.saveProjectUrlToMysql(table=config.MYSQL_PAPER, memo=url)
                    # detail_urls.append(url)

            # 判断是否有下一页
            next_page = self.server.hasNextPage(resp=first_resp.text)
            print(next_page)
            num = 1

            while True:
                # 如果有，请求下一页，获得响应
                if next_page:
                    next_url = next_page
                    print(next_url)
                    # 获取cookie
                    self.cookie_dict = self.download_middleware.create_cookie()
                    next_resp = self.__getResp(func=self.download_middleware.getResp,
                                               url=next_url,
                                               mode='GET',
                                               cookies=self.cookie_dict)
                    num += 1
                    # 如果响应获取失败，跳过这一页，获取下一页，并记录这一页种子
                    if not next_resp:
                        LOGGING.error('第{}页响应获取失败, url: {}'.format(num, next_url))
                        continue

                    # 获得响应成功，提取详情页种子
                    next_text = next_resp.text
                    next_urls = self.server.getDetailUrl(resp=next_text, xueke=subject['xueKeLeiBie'])
                    # print(next_urls)
                    for url in next_urls:
                        # 保存url
                        self.num += 1
                        LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                        LOGGING.info('已存储种子: {}'.format(url))
                        self.dao.saveProjectUrlToMysql(table=config.MYSQL_PAPER, memo=url)
                        # detail_urls.append(url)

                    # print(len(detail_urls))

                    # 判断是否有下一页
                    next_page = self.server.hasNextPage(resp=next_text)

                    # break
                else:
                    LOGGING.info('已翻到最后一页')
                    break

            # print(len(detail_urls))
            #
            break

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
