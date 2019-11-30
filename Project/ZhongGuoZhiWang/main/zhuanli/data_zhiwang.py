# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import hashlib
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhongGuoZhiWang.middleware import download_middleware
from Project.ZhongGuoZhiWang.service import service
from Project.ZhongGuoZhiWang.dao import dao
from Project.ZhongGuoZhiWang import config

log_file_dir = 'ZhiWang'  # LOG日志存放路径
LOGNAME = '<知网_发明公开_data>'  # LOG名
NAME = '知网_发明公开_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
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

    def __getResp(self, func, url, mode, s=None, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, s=s, data=data, cookies=cookies)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None

    def handle(self, response, save_data, url):
        # 获取标题
        save_data['title'] = self.server.getTitle(response)
        # 获取申请号
        save_data['shenQingHao'] = self.server.getField(response, '申请号')
        # 获取申请日
        save_data['shenQingRi'] = self.server.getField(response, '申请日') + ' ' + '00:00:00'
        # 获取公开号
        save_data['gongKaiHao'] = self.server.getField(response, '公开号')
        # 获取公开日
        save_data['gongKaiRi'] = self.server.getField(response, '公开日') + ' ' + '00:00:00'
        # 获取申请人
        save_data['shenQingRen'] = self.server.getField(response, '申请人')
        # 获取发明人
        save_data['faMingRen'] = self.server.getField(response, '发明人')
        # 获取国际专利分类号
        fen_lei_hao = self.server.getField(response, '分类号')
        if '-' in fen_lei_hao:
            save_data['LOCFenLeiHao'] = fen_lei_hao
        else:
            save_data['IPCFenLeiHao'] = fen_lei_hao
        # 获取优先权
        save_data['youXianQuan'] = self.server.getField(response, '优先权')
        # 获取欧洲专利附加分类号
        save_data['ouZhouZhuanLiFuJiaFenLeiHao'] = ''
        # 获取欧洲主分类
        save_data['ouZhouZhuanLiZhuFenLeiHao'] = self.server.getField(response, '欧洲主分类')
        # 获取欧洲副分类
        save_data['ouZhouZhuanLiFuFenLeiHao'] = self.server.getField(response, '欧洲副分类')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getField(response, '摘要')
        # 获取专利国别
        save_data['zhuanLiGuoBie'] = self.server.getZhuanLiGuoBie(save_data['gongKaiHao'])
        # 获取下载
        save_data['xiaZai'] = self.server.getXiaZai(response)
        save_data['guanLianTongZuZhuanLi'] = []
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

    def getTzzl2(self, response, save_data, cookies):

        # 获取字段数据
        self.server.getTzzl2(resp=response, save_data=save_data)

        # 获取下一页
        next_page = self.server.getNextPage(response)
        if next_page:
            next_page_resp = self.__getResp(func=self.download_middleware.getResp,
                                            url=next_page,
                                            mode='GET',
                                            cookies=cookies)
            if next_page_resp:
                next_page_response = next_page_resp.text
                self.getTzzl2(response=next_page_response, save_data=save_data, cookies=cookies)

    def run(self, url):
        save_data = {}
        # 获取首页响应
        resp = self.__getResp(func=self.download_middleware.getResp, url=url, mode='GET')
        if not resp:
            LOGGING.error('首页响应获取失败, url: {}'.format(url))
            return

        response = resp.text
        # 获取字段
        self.handle(response=response, save_data=save_data, url=url)

        # # 获取cookie
        # cookies = self.server.getCookie(resp=resp)
        # # 获取post请求参数
        # data = self.server.getPostData(response)
        # # 获取同族专利首页数据
        # tzzl_index_resp = self.__getResp(func=self.download_middleware.getResp,
        #                                  url=self.index_tzzl_url,
        #                                  mode='POST',
        #                                  data=data,
        #                                  cookies=cookies)
        # if not tzzl_index_resp:
        #     LOGGING.error('同族专利首页数据获取失败。')
        #     # 保存数据
        #     self.dao.saveDataToHbase(data=save_data)
        #     return
        #
        # tzzl_index_response = tzzl_index_resp.text
        # # 获取'更多页url'
        # more_page_url = self.server.getMorePageUrl(tzzl_index_response)
        # if more_page_url:
        #     # 进入更多页
        #     more_page_resp = self.__getResp(func=self.download_middleware.getResp,
        #                                     url=more_page_url,
        #                                     mode='GET',
        #                                     cookies=cookies)
        #     if not more_page_resp:
        #         # 保存数据
        #         self.dao.saveDataToHbase(data=save_data)
        #         return
        #     more_page_response = more_page_resp.text
        #     # 获取同族专利
        #     self.getTzzl2(response=more_page_response, save_data=save_data, cookies=cookies)
        #
        # else:
        #     # 获取当前页显示的所有同族专利
        #     self.server.getTzzl1(resp=tzzl_index_response, save_data=save_data)

        # 保存数据到Hbase
        self.dao.saveDataToHbase(data=save_data)

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_TASK, url=url)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_TASK, count=100, lockname=config.REDIS_TASK_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            # 创建线程池
            threadpool = ThreadPool()
            for url in task_list:
                threadpool.apply_async(func=self.run, args=(url,))

            threadpool.close()
            threadpool.join()

            time.sleep(1)


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(url='http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?dbname=SOPD&filename=EP1140158')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.DATA_SCRIPT_PROCESS)
    for i in range(config.DATA_SCRIPT_PROCESS):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
