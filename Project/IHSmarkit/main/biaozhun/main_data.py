# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import copy
import traceback
import hashlib
import datetime
import asyncio
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.IHSmarkit.middleware import download_middleware
from Project.IHSmarkit.service import service
from Project.IHSmarkit.dao import dao
from Project.IHSmarkit import config

log_file_dir = 'IHSmarkit'  # LOG日志存放路径
LOGNAME = '<IHSmarkit_标准_data>'  # LOG名
NAME = 'IHSmarkit_标准_data'  # 爬虫名
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
        self.server = service.BiaoZhunServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # self.cookie_dict = ''

    def __getResp(self, func, url, mode, data=None, cookies=None):
        # while 1:
        # 最多访问页面10次
        for i in range(10):
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
        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return None

    # 获取价格实体字段
    def price(self, select, title, url):
        price_data = {}
        # 标题
        price_data['title'] = title
        # 价格
        price_data['jiaGe'] = self.server.getJiaGe(select)
        # 关联标准
        price_data['guanLianBiaoZhun'] = self.server.guanLianBiaoZhun(select, url)
        # ===================公共字段
        # url
        price_data['url'] = url
        # 生成key
        price_data['key'] = url
        # 生成sha
        price_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 生成ss ——实体
        price_data['ss'] = '价格'
        # 生成clazz ——层级关系
        price_data['clazz'] = '价格'
        # 生成es ——栏目名称
        price_data['es'] = '标准'
        # 生成ws ——目标网站
        price_data['ws'] = 'IHS markit'
        # 生成biz ——项目
        price_data['biz'] = '文献大数据'
        # 生成ref
        price_data['ref'] = ''

        # 保存数据到Hbase
        self.dao.saveDataToHbase(data=price_data)

    # 获取标准实体字段
    def standard(self, save_data, select, html, url):
        # 获取标准编号
        save_data['biaoZhunBianHao'] = self.server.getBiaoZhunBianHao(select)
        # 获取标题
        save_data['title'] = self.server.getTitle(select)
        # 获取版本
        save_data['banBen'] = self.server.getBanBen(select)
        # 获取出版日期
        save_data['chuBanRiQi'] = self.server.getField(select, 'Published Date')
        # 获取标准状态
        save_data['biaoZhunZhuangTai'] = self.server.getField(select, 'Status')
        # 获取语种
        save_data['yuZhong'] = self.server.getField(select, 'Document Language')
        # 获取标准发布组织
        save_data['biaoZhunFaBuZuZhi'] = self.server.getFaBuZuZhi(select)
        # 获取页数
        save_data['yeShu'] = self.server.getField(select, 'Page Count')
        # 获取摘要
        save_data['ZhaiYao'] = self.server.getZhaiYao(html)
        # 获取被代替标准
        save_data['beiDaiTiBiaoZhun'] = self.server.getBeiDaiTiBiaoZhun(select)
        # 获取代替标准
        save_data['daiTiBiaoZhun'] = self.server.getDaiTiBiaoZhun(select)
        # 获取关联机构
        save_data['guanLianJiGou'] = self.server.guanLianJiGou(select)

        # ============价格实体
        self.price(select, save_data['title'], url)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # # 获取cookie
        # self.cookie_dict = self.download_middleware.create_cookie()
        # # cookie创建失败，停止程序
        # if not self.cookie_dict:
        #     # 逻辑删除任务
        #     self.dao.deleteLogicTask(table=config.MYSQL_STANTARD, sha=sha)
        #     return

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_STANTARD, sha=sha)
            return

        response = resp.text
        # print(response)
        with open('index.html', 'w') as f:
            f.write(response)

        # 转为selector选择器
        selector = self.server.getSelector(response)

        self.standard(save_data=save_data, select=selector, html=response, url=url)

        # ===================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '标准'
        # 生成clazz ——层级关系
        save_data['clazz'] = '标准_国际标准'
        # 生成es ——栏目名称
        save_data['es'] = '标准'
        # 生成ws ——网站名称
        save_data['ws'] = 'IHS markit'
        # 生成biz ——项目名称
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 返回sha为删除任务做准备
        return sha

    def run(self, task):
        # 创建数据存储字典
        save_data = {}

        # 获取字段值存入字典并返回sha
        sha = self.handle(task=task, save_data=save_data)

        # 保存数据到Hbase
        self.dao.saveDataToHbase(data=save_data)

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_STANTARD, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_STANTARD, count=10, lockname=config.REDIS_STANTARD_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            # 创建线程池
            threadpool = ThreadPool()
            for task in task_list:
                threadpool.apply_async(func=self.run, args=(task,))

            threadpool.close()
            threadpool.join()

            time.sleep(1)


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{\"url\": \"https://global.ihs.com/doc_detail.cfm?&rid=IHS&input_search_filter=%28NFPA%29&input_doc_number=&input_doc_title=&org_code=%28NFPA%29&document_name=NFPA%20T2%2E13%2E5&item_s_key=00130382&item_key_date=871231&origin=DSSC\"}')
        # main.run(task='{\"url\": \"https://global.ihs.com/doc_detail.cfm?&rid=IHS&input_search_filter=ISO&item_s_key=00286778&item_key_date=060530&input_doc_number=&input_doc_title=&org_code=ISO\"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()

    po = Pool(1)
    for i in range(1):
        po.apply_async(func=process_start)

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
