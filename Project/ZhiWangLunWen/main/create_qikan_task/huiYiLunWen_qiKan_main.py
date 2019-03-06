# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<会议论文_期刊任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.HuiYiLunWen_QiKanTaskDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_QiKanTaskServer(logging=LOGGING)
        self.dao = dao.HuiYiLunWen_QiKanTaskDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化导航栏url
        self.daoHangUrl = 'http://navi.cnki.net/knavi/Common/LeftNavi/DPaper1'
        # 初始化论文集列表页url
        self.lunWenJiUrl = 'http://navi.cnki.net/knavi/Common/Search/DPaper1'

    # 获取学科导航的最底层导航列表
    def getNavigationList(self, data):
        # 获取导航栏响应
        resp = self.download_middleware.getResp(url=self.daoHangUrl, mode='post', data=data)
        if resp['status'] == 0:
            daoHangResp = resp['data'].content.decode('utf-8')
            # 获取学科导航的最底层导航列表
            navigation_list = self.server.getNavigationList(resp=daoHangResp)
            if navigation_list:

                return navigation_list

            else:
                LOGGING.error('学科导航的最底层导航列表获取失败')
                return []
        else:
            LOGGING.error('导航栏响应获取失败。')
            return []

    # 获取论文集列表
    def handle(self, data):
        request_data = data
        return_data = []
        # 获取论文集列表首页响应
        index_resp = self.download_middleware.getResp(url=self.lunWenJiUrl, mode='post', data=request_data)
        if index_resp['status'] == 0:
            resp = index_resp['data'].content.decode('utf-8')
            # 获取文集数量
            huiYiWenJi_Number = self.server.getHuiYiWenJiNumber(resp=resp)
            if huiYiWenJi_Number:
                # 生成文集总页数
                page_number = self.server.getWenJiPageNumber(huiYiWenJi_Number)
                # 翻页
                for page in range(page_number):
                    # 设置当前页
                    current_page = page + 1
                    data['pageindex'] = current_page
                    page_resp = self.download_middleware.getResp(url=self.lunWenJiUrl, mode='post', data=request_data)
                    page_resp_str = page_resp['data'].content.decode('utf-8')
                    # 获取会议文集种子
                    wenji_url_list = self.server.getWenJiUrlList(resp=page_resp_str)
                    for wenji_url in wenji_url_list:
                        return_data.append(wenji_url)

            else:
                LOGGING.error('文集数量获取失败, 请求参数: {}'.format(request_data))

                return return_data
        else:
            LOGGING.error('论文集首页响应获取失败, 请求参数: {}'.format(request_data))

            return return_data

        return return_data

    def start(self):
        # 生成导航栏页面post请求参数
        daohang_page_data = self.server.getDaoHangPageData()
        # 获取学科导航的最底层导航列表
        navigation_list = self.getNavigationList(daohang_page_data)
        for navigation in navigation_list:
            lanmu_name = navigation['lanmu_name']
            # 生成论文集列表首页请求参数
            lunWenJi_UrlData = self.server.getLunWenJiUrlData(data=navigation, page=1)
            # 获取论文集url列表
            url_list = self.handle(lunWenJi_UrlData)
            for url_data in url_list:
                # 保存论文集url到mysql
                self.dao.saveLunWenJiUrl(url_data=url_data)


def process_start():
    main = SpiderMain()
    main.start()

if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.HUIYILUNWEN_QIKANRENWU_PROCESS_NUMBER)
    for i in range(config.HUIYILUNWEN_QIKANRENWU_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
