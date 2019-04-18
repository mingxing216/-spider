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
from Test.ZhiWangZhuanLi.middleware import download_middleware
from Test.ZhiWangZhuanLi.service import service
from Test.ZhiWangZhuanLi.dao import dao
from Test.ZhiWangZhuanLi import config

log_file_dir = 'ZhiWangZhuanLi'  # LOG日志存放路径
LOGNAME = '<知网_海外专利_task>'  # LOG名
NAME = '知网_海外专利_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.TaskDownloader(logging=LOGGING,
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

    # 网页正常度检测机制
    def __judge_verify(self, param):
        # 下载
        resp = self._startDownload(param=param)
        if resp['status'] == 0:
            response = resp['data']
            if '请输入验证码' in response.text or len(response.text) < 20:
                self.logging.info('出现验证码')
                # 重新下载
                return {'status': 2}

        return resp


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.country_number = 14  # 国家数
        self.index_url = 'http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SOPD'
        self.cookie = ''
        self.number = 0

    # 获取下一页响应
    def getNextPageResp(self, url):
        while 1:
            next_resp = self.download_middleware.getNextHtml(url=url, cookie=self.cookie)
            if next_resp['status'] == 0:
                return next_resp['data'].text
            if next_resp['status'] == 1:
                return None
            if next_resp['status'] == 2:
                # 生成新的cookie
                self.cookie = self.download_middleware.create_cookie()
                print('新的cookie: {}'.format(self.cookie))
                continue


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

            # if next_url:
            #     new_resp = self.getNextPageResp(url=next_url)
            #     if new_resp is None:
            #         break
            #
            #     next_resp = new_resp
            #
            #     # # 获取下一页url
            #     # next_page_url = self.server.getNextUrl(resp=new_resp)
            #     # if next_page_url is None:
            #     #     break
            #     # # 替换页码获得新的下一页地址
            #     # next_url = self.server.replace_page_number(next_page_url, page + 1)
            #     # print('旧下一页: {}'.format(next_page_url))
            #     # print('新下一页: {}'.format(next_url))
            #     #
            #     #     next = self.download_middleware.getNextHtml(url=next_url, cookie=self.cookie)
            #     #     if next['status'] == 0:
            #     #         next_resp = next['data'].text
            #     #     else:
            #     #         break
            #     page += 1
            #     continue
            #
            # else:
            #     break

            if next_url:
                # 下载下一页响应
                next_respon = self.download_middleware.getNextHtml(url=next_url, cookie=self.cookie)

                if next_respon['status'] == 0:
                    next_resp = next_respon['data'].text
                elif next_respon['status'] == 2:
                    print('换个cookie')
                    # 生成新的cookie
                    self.cookie = self.download_middleware.create_cookie()
                    self.download_middleware.getTimeListResp(category=category, country=country, cookie=self.cookie)
                    # 获取首页响应
                    index_resp = self.download_middleware.getIndexHtml(year=year, cookie=self.cookie)
                    print('首页响应: {}'.format(index_resp))
                    if index_resp['status'] == 0:
                        index_response = index_resp['data'].text
                    else:
                        index_response = ''
                    # 获取下一页url
                    next_page_url = self.server.getNextUrl(resp=index_response)
                    if next_page_url is None:
                        break
                    # 替换页码获得新的下一页地址
                    next_url = self.server.replace_page_number(next_page_url, page + 1)
                    print('旧下一页: {}'.format(next_page_url))
                    print('新下一页: {}'.format(next_url))

                    next = self.download_middleware.getNextHtml(url=next_url, cookie=self.cookie)
                    if next['status'] == 0:
                        next_resp = next['data'].text
                    else:
                        break
                page += 1
                continue

            else:
                break

        return return_data

    def start(self):
        category_number = ['A01B', 'A01C', 'A01D', 'A01F', 'A01G', 'A01H', 'A01J', 'A01K', 'A01L', 'A01M', 'A01N',
                           'A01P', 'A21B', 'A21C', 'A21D', 'A22B', 'A22C', 'A23B', 'A23C', 'A23D', 'A23F', 'A23G',
                           'A23J', 'A23K', 'A23L', 'A23N', 'A23P', 'A24B', 'A24C', 'A24D', 'A24F', 'A41B', 'A41C',
                           'A41D', 'A41F', 'A41G', 'A41H', 'A42B', 'A42C', 'A43B', 'A43C', 'A43D', 'A44B', 'A44C',
                           'A45B', 'A45C', 'A45D', 'A45F', 'A46B', 'A46D', 'A47B', 'A47C', 'A47D', 'A47F', 'A47G',
                           'A47H', 'A47J', 'A47K', 'A47L', 'A61B', 'A61C', 'A61D', 'A61F', 'A61G', 'A61H', 'A61J',
                           'A61K', 'A61L', 'A61M', 'A61N', 'A61P', 'A61Q', 'A62B', 'A62C', 'A62D', 'A63B', 'A63C',
                           'A63D', 'A63F', 'A63G', 'A63H', 'A63J', 'A63K', 'A99Z', 'B01B', 'B01D', 'B01F', 'B01J',
                           'B01L', 'B02B', 'B02C', 'B03B', 'B03C', 'B03D', 'B04B', 'B04C', 'B05B', 'B05C', 'B05D',
                           'B09B', 'B09C', 'B21B', 'B21C', 'B21D', 'B21F', 'B21G', 'B21H', 'B21J', 'B21K', 'B21L',
                           'B22C', 'B26B', 'B26D', 'B26F', 'B27B', 'B27C', 'B27D', 'B27F', 'B27G', 'B27H', 'B27J',
                           'B27K', 'B27L', 'B27M', 'B27N', 'B28B', 'B28C', 'B28D', 'B29B', 'B29C', 'B29D', 'B29K',
                           'B29L', 'B30B', 'B31B', 'B31C', 'B31D', 'B31F', 'B32B', 'B41B', 'B41C', 'B41D', 'B41F',
                           'B41G', 'B41J', 'B41K', 'B41L', 'B41M', 'B41N', 'B42B', 'B42C', 'B42D', 'B42F', 'B43K',
                           'B43L', 'B43M', 'B44B', 'B44C', 'B44D', 'B44F', 'B60B', 'B60C', 'B60D', 'B60F', 'B60G',
                           'B60H', 'B60J', 'B60K', 'B60L', 'B60M', 'B60N', 'B60P', 'B60Q', 'B60R', 'B60S', 'B60T',
                           'B60V', 'B60W', 'B61B', 'B61C', 'B61D', 'B61F', 'B61G', 'B61H', 'B61J', 'B61K', 'B61L',
                           'B62B', 'B62C', 'B62D', 'B62H', 'B62J', 'B62K', 'B62L', 'B62M', 'B63B', 'B63C', 'B63G',
                           'B63H', 'B63J', 'B64B', 'B64C', 'B64D', 'B64F', 'B64G', 'B65B', 'B65C', 'B65D', 'B65F',
                           'B65G', 'B65H', 'B66B', 'B66C', 'B66D', 'B66F', 'B67B', 'B67C', 'B67D', 'B68B', 'B68C',
                           'B68F', 'B68G', 'B81B', 'B81C', 'B82B', 'B06B', 'B07B', 'B07C', 'B08B', 'B23B', 'B23C',
                           'B23D', 'B23F', 'B23G', 'B23H', 'B23K', 'B23P', 'B23Q', 'B24B', 'B24C', 'B24D', 'B25B',
                           'B25C', 'B25D', 'B25F', 'B25G', 'B25H', 'B25J', 'B99Z', 'C01B', 'C01C', 'C01D', 'C01F',
                           'C01G', 'C02F', 'C03B', 'C03C', 'C04B', 'C05B', 'C05C', 'C05D', 'C05F', 'C05G', 'C06B',
                           'C06C', 'C06D', 'C06F', 'C07B', 'C07C', 'C07D', 'C07F', 'C07G', 'C07H', 'C07J', 'C07K',
                           'C08B', 'C08C', 'C08F', 'C08G', 'C08H', 'C08J', 'C08K', 'C08L', 'C09B', 'C09C', 'C09D',
                           'C09F', 'C09G', 'C09H', 'C09J', 'C09K', 'C10B', 'C10C', 'C10F', 'C10G', 'C10H', 'C10J',
                           'C10K', 'C10L', 'C10M', 'C10N', 'C11B', 'C11C', 'C11D', 'C12C', 'C12F', 'C12G', 'C12H',
                           'C12J', 'C12L', 'C12M', 'C12N', 'C12P', 'C12Q', 'C12R', 'C12S', 'C13C', 'C13D', 'C13F',
                           'C13G', 'C13H', 'C13J', 'C13K', 'C14B', 'C14C', 'C21B', 'C21C', 'C21D', 'C22B', 'C22C',
                           'C22F', 'C23C', 'C23D', 'C23F', 'C23G', 'C25B', 'C25C', 'C25D', 'C25F', 'C30B', 'C40B',
                           'C99Z', 'D01B', 'D01C', 'D01D', 'D01F', 'D01G', 'D01H', 'D02G', 'D02H', 'D02J', 'D03C',
                           'D03D', 'D03J', 'D04B', 'D04C', 'D04D', 'D04G', 'D04H', 'D05B', 'D05C', 'D06B', 'D06C',
                           'D06F', 'D06G', 'D06H', 'D06J', 'D06L', 'D06M', 'D06N', 'D06P', 'D06Q', 'D07B', 'D21B',
                           'D21C', 'D21D', 'D21F', 'D21G', 'D21H', 'D21J', 'D99Z', 'E01B', 'E01C', 'E01D', 'E01F',
                           'E01H', 'E02B', 'E02C', 'E02D', 'E02F', 'E03B', 'E03C', 'E03D', 'E03F', 'E04B', 'E04C',
                           'E04D', 'E04F', 'E04G', 'E04H', 'E05B', 'E05C', 'E05D', 'E05F', 'E05G', 'E06B', 'E06C',
                           'E21B', 'E21C', 'E21D', 'E21F', 'E99Z', 'F01B', 'F01C', 'F01D', 'F01K', 'F01L', 'F01M',
                           'F01N', 'F01P', 'F02B', 'F02C', 'F02D', 'F02F', 'F02G', 'F02K', 'F02M', 'F02N', 'F02P',
                           'F03B', 'F03C', 'F03D', 'F03G', 'F03H', 'F04B', 'F04C', 'F04D', 'F04F', 'F15B', 'F15C',
                           'F15D', 'F16B', 'F16C', 'F16D', 'F16F', 'F16G', 'F16H', 'F16J', 'F16K', 'F16L', 'F16M',
                           'F16N', 'F16P', 'F16S', 'F16T', 'F17B', 'F17C', 'F17D', 'F21H', 'F21K', 'F21L', 'F21S',
                           'F21V', 'F21W', 'F21Y', 'F22B', 'F22D', 'F22G', 'F23B', 'F23C', 'F23D', 'F23G', 'F23H',
                           'F23J', 'F23K', 'F23L', 'F23M', 'F23N', 'F23Q', 'F23R', 'F24B', 'F24C', 'F24D', 'F24F',
                           'F24H', 'F24J', 'F25B', 'F25C', 'F25D', 'F25J', 'F26B', 'F27B', 'F27D', 'F28B', 'F28C',
                           'F28D', 'F28F', 'F28G', 'F41A', 'F41B', 'F41C', 'F41F', 'F41G', 'F41H', 'F41J', 'F42B',
                           'F42C', 'F42D', 'F99Z', 'G01B', 'G01C', 'G01D', 'G01F', 'G01G', 'G01H', 'G01J', 'G01K',
                           'G01L', 'G01M', 'G01N', 'G01P', 'G01R', 'G01S', 'G01T', 'G01V', 'G01W', 'G02B', 'G02C',
                           'G02F', 'G03B', 'G03C', 'G03D', 'G03F', 'G03G', 'G03H', 'G04B', 'G04C', 'G04D', 'G04F',
                           'G04G', 'G05B', 'G05D', 'G05F', 'G05G', 'G06C', 'G06D', 'G06E', 'G06F', 'G06G', 'G06J',
                           'G06K', 'G06M', 'G06N', 'G06T', 'G06Q', 'G07B', 'G07C', 'G07D', 'G07F', 'G07G', 'G08B',
                           'G08C', 'G08G', 'G09B', 'G09C', 'G09D', 'G09F', 'G09G', 'G10B', 'G10C', 'G10D', 'G10F',
                           'G10G', 'G10H', 'G10K', 'G10L', 'G11B', 'G11C', 'G12B', 'G21B', 'G21C', 'G21D', 'G21F',
                           'G21G', 'G21H', 'G21J', 'G21K', 'G99Z', 'H01B', 'H01C', 'H01F', 'H01G', 'H01H', 'H01K',
                           'H01L', 'H01M', 'H01P', 'H01Q', 'H01R', 'H01S', 'H01T', 'H01J', 'H02B', 'H02G', 'H02H',
                           'H02J', 'H02K', 'H02M', 'H02N', 'H02P', 'H03B', 'H03C', 'H03D', 'H03F', 'H03G', 'H03H',
                           'H03J', 'H03K', 'H03L', 'H03M', 'H04B', 'H04H', 'H04J', 'H04K', 'H04L', 'H04M', 'H04N',
                           'H04Q', 'H04R', 'H04S', 'H05B', 'H05C', 'H05F', 'H05G', 'H05H', 'H05K', 'H99Z']
        # category_number = []
        #
        # index_resp = self.download_middleware.getResp(url=self.index_url, mode='GET')
        # if index_resp['status'] == 0:
        #     index_response = index_resp['data'].text
        #     # 获取第一分类列表
        #     first_list = self.server.getIndexClassList(resp=index_response)
        #     for first_url in first_list:
        #         first_resp = self.download_middleware.getResp(url=first_url, mode='GET')
        #         if first_resp['status'] == 0:
        #             first_response = first_resp['data'].text
        #             # 获取第二分类列表
        #             second_list = self.server.getSecondClassList(resp=first_response)
        #             for second_url in second_list:
        #                 second_resp = self.download_middleware.getResp(url=second_url, mode='GET')
        #                 if second_resp['status'] == 0:
        #                     second_response = second_resp['data'].text
        #                     # 获取第三分类号
        #                     category_list = self.server.getCategoryNumber(resp=second_response)
        #                     for category in category_list:
        #                         category_number.append(category)
        #                 else:
        #                     LOGGING.error('第二分类页获取失败')
        #                     continue
        #         else:
        #             LOGGING.error('第一分类页获取失败')
        #             continue
        # else:
        #     LOGGING.error('首页响应获取失败')
        #     return
        #
        # if not category_number:
        #     LOGGING.error('category_number is None')

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
                time_response = self.download_middleware.getTimeListResp(category=category, country=number,
                                                                         cookie=self.cookie)
                if time_response is None:
                    continue

                year_list = self.server.getYearList(resp=time_response)
                for year in year_list:
                    # 获取指定年的专利列表首页响应
                    index_resp = self.download_middleware.getIndexHtml(year=year, cookie=self.cookie)
                    if index_resp['status'] == 0:
                        index_response = index_resp['data'].text

                    else:
                        index_response = None

                    if not index_response:
                        continue

                    # 获取专利主页url，内置翻页功能
                    try:
                        url_list = self.getUrlList(index_response, category=category, country=number, year=year)
                    except Exception as e:
                        LOGGING.error(e)
                        url_list = []

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
