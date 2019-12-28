# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<学位论文_期刊任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.XueWeiLunWen_QiKanTaskDownloader(logging=LOGGING,
                                                                                        proxy_type=config.PROXY_TYPE,
                                                                                        timeout=config.TIMEOUT,
                                                                                        proxy_country=config.COUNTRY)
        self.server = service.XueWeiLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.XueWeiLunWen_QiKanTaskDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 地域导航页url
        self.index_url = 'http://navi.cnki.net/knavi/Common/LeftNavi/PPaper'
        # 单位列表页url
        self.page_url = 'http://navi.cnki.net/knavi/Common/Search/PPaper'

    def start(self):
        # 生成导航栏页面post请求参数
        index_url_data = self.server.getIndexUrlData()
        # 获取地域导航页响应
        index_resp = self.download_middleware.getResp(url=self.index_url, mode='post', data=index_url_data)
        if index_resp['status'] == 0:
            index_resp = index_resp['data'].content.decode('utf-8')
            # 获取分类参数
            fenlei_data_list = self.server.getFenLeiDataList(resp=index_resp)
            for fenlei_data in fenlei_data_list:
                # 生成单位列表页参数
                danwei_list_url_data = self.server.getDanWeiListUrlData(data=fenlei_data, page=1)
                # 获取单位列表首页响应
                danwei_index_page_resp = self.download_middleware.getResp(url=self.page_url, mode='post',
                                                                          data=danwei_list_url_data)
                if danwei_index_page_resp['status'] == 0:
                    danwei_index_resp = danwei_index_page_resp['data'].content.decode('utf-8')
                    # 获取单位数量
                    danwei_number = int(self.server.getDanWeiNumber(resp=danwei_index_resp))
                    if danwei_number > 0:
                        # 获取总页数
                        page_number = self.server.getPageNumber(danwei_number=danwei_number)
                        for page in range(page_number):
                            page += 1
                            data = self.server.getDanWeiListUrlData(data=fenlei_data, page=page)
                            # 获取列表页响应
                            danwei_list_resp = self.download_middleware.getResp(url=self.page_url,
                                                                                mode='post',
                                                                                data=data)
                            if danwei_list_resp['status'] == 0:
                                danwei_list_resp = danwei_list_resp['data'].content.decode('utf-8')
                                # 获取单位url
                                danwei_url_list = self.server.getDanWeiUrlList(resp=danwei_list_resp)
                                for danwei_url in danwei_url_list:
                                    # 数据存储
                                    self.dao.saveDanWeiUrl(danwei_url)
                                    # LOGGING.info(danwei_url)
                                    # print(danwei_url)

                            else:
                                LOGGING.error('单位列表页响应获取失败, url: {}, data: {}'.format(self.page_url, data))
                else:
                    LOGGING.error('单位列表首页响应获取失败, url: {}, data: {}'.format(self.page_url, danwei_list_url_data))
        else:
            LOGGING.error('地域导航页响应获取失败，url: {}, data: {}'.format(self.index_url, index_url_data))


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.XUEWEILUNWEN_QIKANRENWU_PROCESS_NUMBER)
    for i in range(config.XUEWEILUNWEN_QIKANRENWU_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
