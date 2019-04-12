# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import ast
import hashlib
import pprint
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.WanFangBiaoZhun.middleware import download_middleware
from Project.WanFangBiaoZhun.service import service
from Project.WanFangBiaoZhun.dao import dao
from Project.WanFangBiaoZhun import config

log_file_dir = 'WanFangBiaoZhun'  # LOG日志存放路径
LOGNAME = '<万方_标准数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Data_Downloader(logging=LOGGING,
                                                                       update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                       proxy_type=config.PROXY_TYPE,
                                                                       timeout=config.TIMEOUT,
                                                                       retry=config.RETRY,
                                                                       proxy_country=config.COUNTRY)
        self.server = service.Data_Server(logging=LOGGING)
        self.dao = dao.Data_Dao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        save_data = {}
        task_dict = ast.literal_eval(task_data)
        sha = task_dict['sha']
        url = task_dict['url']

        # 检查当前任务是否被抓取过
        status = self.dao.getTaskStatus(sha=sha)
        if status:
            LOGGING.info('当前任务已抓取过，放弃抓取。sha: {}, url: {}'.format(sha, url))
            return

        # 获取标准主页HTML
        resp = self.download_middleware.getResp(url=url, mode='GET')

        if not resp:
            LOGGING.error('标准主页HTML获取失败，url: {}'.format(url))
            return

        html = resp.text

        # 获取标题
        save_data['title'] = self.server.getTitle(html)
        # 获取英文标题
        save_data['yingWenBiaoTi'] = self.server.getYingWenBiaoTi(html)
        # 获取标准编号
        save_data['biaoZhunBianHao'] = self.server.getBiaoZhunBianHao(html)
        # 获取标准类型
        save_data['biaoZhunLeiXing'] = self.server.getBiaoZhunLeiXing(html)
        # 获取发布日期
        save_data['faBuRiQi'] = self.server.getFaBuRiQi(html)
        # 获取标准状态
        save_data['biaoZhunZhuangTai'] = self.server.getBiaoZhunZhuangTai(html)
        # 获取强制性标准
        save_data['qiangZhiXingBiaoZhun'] = self.server.getQiangZhiXingBiaoZhun(html)
        # 获取实施日期
        save_data['shiShiRiQi'] = self.server.getShiShiRiQi(html)

        pprint.pprint(save_data)


    def start(self):
        while True:
            # cateid = config.CATEID
            # cateid_pinyin = self.server.getCateidPinyin(cateid)
            #
            # # 从redis队列获取任务
            # task_list = self.dao.getTask(key=cateid_pinyin, count=1, lockname=config.SPIDER_GET_TASK_LOCK)
            #
            # if task_list:
            #     thread_pool = ThreadPool()
            #     for task in task_list:
            #         thread_pool.apply_async(func=self.handle, args=(task,))
            #
            #     thread_pool.close()
            #     thread_pool.join()
            #
            # else:
            #     LOGGING.warning('任务队列暂无数据。')
            #     time.sleep(10)
            #
            #     continue
            self.handle("{'sha': '8cbe068c4cb43abcefaf14e3f1773382a2f94606', 'url': 'http://www.wanfangdata.com.cn/details/detail.do?_type=standards&id=GB%2FT+25608-2010'}")
            # self.handle(
            #     "{'sha': 'a6322323a17edaf2c297a2478b94a70ccf45be53', 'url': 'http://www.wanfangdata.com.cn/details/detail.do?_type=standards&id=NB%2FT+20248-2013'}")

            break



def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.SPIDER_PROCESS)
    for i in range(config.SPIDER_PROCESS):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
