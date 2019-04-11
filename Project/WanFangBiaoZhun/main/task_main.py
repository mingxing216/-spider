# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import re
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.WanFangBiaoZhun.middleware import download_middleware
from Project.WanFangBiaoZhun.service import service
from Project.WanFangBiaoZhun.dao import dao
from Project.WanFangBiaoZhun import config

log_file_dir = 'WanFangBiaoZhun'  # LOG日志存放路径
LOGNAME = '<万方_标准任务>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Task_Downloader(logging=LOGGING,
                                                                       update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                       proxy_type=config.PROXY_TYPE,
                                                                       timeout=config.TIMEOUT,
                                                                       retry=config.RETRY,
                                                                       proxy_country=config.COUNTRY)
        self.server = service.Task_Server(logging=LOGGING)
        self.dao = dao.Task_Dao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

        self.index_url = 'http://www.wanfangdata.com.cn/navigations/standards.do'
        self.zuzhi_url = 'http://www.wanfangdata.com.cn/search/navigation.do'

    def getUrlList(self, zuzhi_url):
        return_data = []
        # 页数
        page = 0
        while 1:
            page += 1
            new_zuzhi_url = re.sub(r"page=.*?&", "page={}&".format(page), zuzhi_url)
            new_zuzhi_page_resp = self.download_middleware.getResp(url=new_zuzhi_url, mode='GET')
            if new_zuzhi_page_resp:
                zuzhi_html = new_zuzhi_page_resp.text
                onclicks = self.server.getOnclick(zuzhi_html)
                if onclicks:
                    save_url_list = self.server.getSaveUrlList(onclicks)
                    return_data += save_url_list
                    continue
                else:
                    break

        return return_data


    def start(self):
        # 获取首页源码
        index_resp = self.download_middleware.getResp(url=self.index_url, mode='GET')
        if index_resp:
            index_html = index_resp.text
            # 获取分类url列表
            type_urllist = self.server.getTypeUrl(index_html)
            if type_urllist:
                for type_url in type_urllist:
                    # 获取各分类主页html
                    type_resp = self.download_middleware.getResp(url=type_url, mode='GET')
                    if type_resp:
                        type_html = type_resp.text
                        # 获取searchWord参数_POST
                        searchWord_post = self.server.getSearchWord_POST(type_html)
                        # 获取searchWord参数_GET
                        searchWord_get = self.server.getSearchWord_GET(type_url)
                        if searchWord_get is None:
                            continue

                        if searchWord_post:
                            # 生成标准组织页请求参数
                            post_data = self.server.getPostData(searchWord_post)
                            # 获取标准组织页响应
                            zuzhi_resp = self.download_middleware.getResp(url=self.zuzhi_url, mode='post', data=post_data)
                            zuzhi_data_json = zuzhi_resp.text
                            # 获取组织分类url
                            zuzhi_url_list = self.server.getZuZhiUrlList(zuzhi_data_json, searchWord_get)
                            for zuzhi_url in zuzhi_url_list:
                                # 获取标准url列表
                                url_list = self.getUrlList(zuzhi_url)
                                for url in url_list:
                                    # 生成要保存的数据集合
                                    save_data = self.server.getSaveData(url)
                                    # 保存任务
                                    self.dao.saveTask(data=save_data, cateid=config.CATEID)
                                time.sleep(config.DOWNLOADDELY)

                                # break

                        else:
                            LOGGING.error('searchWord获取失败, 来源url: {}'.format(type_url))
                    else:
                        LOGGING.error('分类主页HTML获取失败, 来源url: {}'.format(type_url))

                    # break
            else:
                LOGGING.error('分类url列表获取失败')
        else:
            LOGGING.error('首页源码获取失败。')



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
