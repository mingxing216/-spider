# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import hashlib
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangHaiWaiZhuanLi.middleware import download_middleware
from Project.ZhiWangHaiWaiZhuanLi.service import service
from Project.ZhiWangHaiWaiZhuanLi.dao import dao
from Project.ZhiWangHaiWaiZhuanLi import config
from Project.ZhiWangHaiWaiZhuanLi.spider import yc_tzzl_spider

log_file_dir = 'ZhiWangHaiWaiZhuanLi'  # LOG日志存放路径
LOGNAME = '<知网海外专利数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.DataDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.DataServer(logging=LOGGING)
        self.dao = dao.DataDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.tzzl_url = 'http://dbpub.cnki.net/grid2008/dbpub/Detail.aspx?action=node&dbname=sopd&block=SOPD_TZZL'

    def handle(self, resp, save_data):
        # 获取标题
        save_data['title'] = self.server.getTitle(resp)
        # 获取申请号
        save_data['shenQingHao'] = self.server.getField(resp, '申请号')
        # 获取申请日
        save_data['shenQingRi'] = self.server.getField(resp, '申请日') + ' ' + '00:00:00'
        # 获取公开号
        save_data['gongKaiHao'] = self.server.getField(resp, '公开号')
        # 获取公开日
        save_data['gongKaiRi'] = self.server.getField(resp, '公开日') + ' ' + '00:00:00'
        # 获取申请人
        save_data['shenQingRen'] = self.server.getField(resp, '申请人')
        # 获取发明人
        save_data['faMingRen'] = self.server.getField(resp, '发明人')
        # 获取国际专利分类号
        fen_lei_hao = self.server.getField(resp, '分类号')
        if '-' in fen_lei_hao:
            save_data['LOCFenLeiHao'] = fen_lei_hao
        else:
            save_data['IPCFenLeiHao'] = fen_lei_hao
        # 获取优先权
        save_data['youXianQuan'] = self.server.getField(resp, '优先权')
        # 获取欧洲专利附加分类号
        save_data['ouZhouZhuanLiFuJiaFenLeiHao'] = ''
        # 获取欧洲主分类
        save_data['ouZhouZhuanLiZhuFenLeiHao'] = self.server.getField(resp, '欧洲主分类')
        # 获取欧洲副分类
        save_data['ouZhouZhuanLiFuFenLeiHao'] = self.server.getField(resp, '欧洲副分类')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getField(resp, '摘要')
        # 获取专利国别
        save_data['zhuanLiGuoBie'] = self.server.getZhuanLiGuoBie(save_data['gongKaiHao'])
        # 获取下载
        save_data['xiaZai'] = self.server.getXiaZai(resp)

    def run(self, url):
        save_data = {}
        # 下载首页响应
        index_resp = self.download_middleware.getIndexResp(url=url)
        # 获取字段
        self.handle(resp=index_resp, save_data=save_data)
        error_number = 0
        while 1:
            if error_number >= 2:
                break
            # 获取代理
            proxies = self.download_middleware.downloader.proxy_obj.getProxy()
            try:
                yc_tzzl_spider.run(index_resp, proxies, save_data, self.server)
                break

            except Exception as e:
                print(e)
                error_number += 1
                # 删除代理
                self.download_middleware.downloader.proxy_obj.delProxy(proxies)
                continue

        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 生成ss ——实体
        save_data['ss'] = '专利'
        # 生成ws ——目标网站
        save_data['ws'] = '中国知网国外专利'
        # 生成clazz ——层级关系
        save_data['clazz'] = '专利'
        # 生成es ——栏目名称
        save_data['es'] = '专利'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 保存数据
        save_status = self.dao.saveDataToHbase(save_data)

        LOGGING.info(save_status.content.decode('utf-8'))
        # 从mysql删除数据
        self.dao.deleteObject(url=url)


    def start(self):
        # 从redis获取任务
        url_list = self.dao.getUrlList()

        threadpool = ThreadPool()
        for url in url_list:
            threadpool.apply_async(func=self.run, args=(url,))
        threadpool.close()
        threadpool.join()

def process_start():
    main = SpiderMain()
    main.start()

if __name__ == '__main__':
    while 1:
        po = Pool(config.PROCESS_NUMBER)
        for i in range(config.PROCESS_NUMBER):
            po.apply_async(func=process_start)
        po.close()
        po.join()
        time.sleep(2)

