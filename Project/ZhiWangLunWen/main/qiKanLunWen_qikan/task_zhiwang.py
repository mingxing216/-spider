# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import hashlib
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_期刊_task>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.QiKanLunWen_QiKanTaskDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 分类列表url
        self.fenlei_list_url = 'http://navi.cnki.net/knavi/Common/ClickNavi/Journal?'
        # 期刊列表页url
        self.qikan_list_url = 'http://navi.cnki.net/knavi/Common/Search/Journal'

    def __getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(2):
            resp = self.download_middleware.getResp(url=url,
                                                    mode=mode,
                                                    s=s,
                                                    data=data,
                                                    cookies=cookies,
                                                    referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 200 or 'window.location.href' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            return None

    def spider(self, SearchStateJson, page_number):
        for page in range(page_number):
            LOGGING.info('第{}页'.format(page + 1))
            # 期刊列表页的请求data
            data = self.server.getQiKanLieBiaoPageData(SearchStateJson=SearchStateJson, page=page + 1)
            # 期刊列表页的响应
            qikan_profile_resp = self.__getResp(url=self.qikan_list_url,
                                                mode='POST',
                                                data=data)
            if not qikan_profile_resp:
                LOGGING.error('期刊列表页获取失败。data: {}'.format(data['data']))
                yield None

            qikan_profile_text = qikan_profile_resp.text
            yield qikan_profile_text


    def start(self):
        # 生成分类列表页url
        for fenlei_url in self.server.getFenLeiUrl(self.fenlei_list_url):
            # print(fenlei_url)
            # 获取分类页源码
            fenlei_resp = self.__getResp(url=fenlei_url, mode='GET')

            # with open('fenlei.html', 'w', encoding='utf-8') as f:
            #     f.write(fenlei_resp.text)

            if not fenlei_resp:
                LOGGING.error('分类页源码获取失败， url: {}'.format(fenlei_url))
                continue

            fenlei_text = fenlei_resp.text
            # 获取分类数据
            for fenlei_data in self.server.getFenLeiData(resp=fenlei_text, page=1):
                # print(fenlei_data)
                # 分类名
                try:
                    xueKeLeiBie = fenlei_data['xueKeLeiBie']
                except Exception:
                    xueKeLeiBie = ""
                try:
                    heXinQiKan = fenlei_data['heXinQiKan']
                except Exception:
                    heXinQiKan = ""
                SearchStateJson = fenlei_data['SearchStateJson']
                # 获取期刊列表首页响应
                qikan_list_resp = self.__getResp(url=self.qikan_list_url,
                                                 mode='POST',
                                                 data=fenlei_data['data'])
                if not fenlei_resp:
                    LOGGING.error('期刊列表首页响应失败， url: {}'.format(fenlei_url))
                    continue

                # with open('first.html', 'w', encoding='utf-8') as f:
                #     f.write(qikan_list_resp.text)

                qikan_first_text = qikan_list_resp.text
                # 获取总页数
                page_number = self.server.getPageNumber(resp=qikan_first_text)
                # print(page_number)
                # 获取期刊列表页响应
                for resp in self.spider(SearchStateJson=SearchStateJson, page_number=page_number):
                    # 获取期刊列表
                    for task in self.server.getQiKanList(resp=resp):
                        # 保存数据
                        task['s_xueKeLeiBie'] = xueKeLeiBie
                        task['s_zhongWenHeXinQiKanMuLu'] = heXinQiKan
                        # print(task)
                        self.dao.saveTaskToMysql(table=config.MYSQL_MAGAZINE, memo=task, ws='中国知网', es='期刊')

def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
