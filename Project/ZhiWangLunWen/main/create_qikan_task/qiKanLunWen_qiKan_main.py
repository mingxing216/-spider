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
LOGNAME = '<期刊论文_期刊任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.QiKanLunWen_QiKanTaskDownloader(logging=LOGGING,
                                                                                       update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                                       proxy_type=config.PROXY_TYPE,
                                                                                       timeout=config.TIMEOUT,
                                                                                       retry=config.RETRY,
                                                                                       proxy_country=config.COUNTRY)
        self.server = service.QiKanLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.QiKanLunWen_QiKanTaskDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 分类列表url
        self.fenlei_list_url = 'http://navi.cnki.net/knavi/Common/ClickNavi/Journal?'
        # 期刊列表页url
        self.qikan_list_url = 'http://navi.cnki.net/knavi/Common/Search/Journal'

    def spider(self, SearchStateJson, page_number):
        for page in range(page_number):
            LOGGING.info('第{}页'.format(page + 1))
            # 期刊列表页的请求data
            data = self.server.getQiKanLieBiaoPageData(SearchStateJson=SearchStateJson, page=page + 1)
            # 期刊列表页的响应
            qikan_list_page_resp = self.download_middleware.getResp(url=self.qikan_list_url,
                                                                    mode='post',
                                                                    data=data)
            if qikan_list_page_resp['status'] == 0:
                qikan_list_page_resp = qikan_list_page_resp['data'].content.decode('utf-8')
                yield qikan_list_page_resp

            else:
                LOGGING.error('期刊列表页获取失败。data: {}'.format(data['data']))
                yield None


    def start(self):
        # 生成分类列表页url
        for fenlei_url in self.server.getFenLeiUrl(self.fenlei_list_url):
            # 获取分类页源码
            fenlei_resp = self.download_middleware.getResp(url=fenlei_url, mode='get')
            if fenlei_resp['status'] == 0:
                fenlei_resp = fenlei_resp['data'].content.decode('utf-8')
                # 获取分类数据
                for fenlei_data in self.server.getFenLeiData(resp=fenlei_resp, page=1):
                    # 分类名
                    column_name = fenlei_data['column_name']
                    SearchStateJson = fenlei_data['SearchStateJson']
                    # 获取期刊列表首页响应
                    qikan_list_resp = self.download_middleware.getResp(url=self.qikan_list_url,
                                                                       mode='post',
                                                                       data=fenlei_data['data'])
                    if qikan_list_resp['status'] == 0:
                        qikan_list_resp = qikan_list_resp['data'].content.decode('utf-8')
                        # 获取总页数
                        page_number = self.server.getPageNumber(resp=qikan_list_resp)
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
                                self.dao.saveData(sha=sha, memo=data)

                    # break
            else:
                LOGGING.error('分类页源码获取失败， url: {}'.format(fenlei_url))
                continue

            # break


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.QIKANLUNWEN_QIKANRENWU_PROCESS_NUMBER)
    for i in range(config.QIKANLUNWEN_QIKANRENWU_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
