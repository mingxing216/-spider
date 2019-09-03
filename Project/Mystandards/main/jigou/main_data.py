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
import gevent
from gevent import monkey
# 猴子补丁一定要先打，不然就会报错
monkey.patch_all()

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Mystandards.middleware import download_middleware
from Project.Mystandards.service import service
from Project.Mystandards.dao import dao
from Project.Mystandards import config

log_file_dir = 'Mystandards'  # LOG日志存放路径
LOGNAME = 'Mystandards_机构_data'  # LOG名
NAME = 'Mystandards_机构_data'  # 爬虫名
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
        self.server = service.JiGouServer(logging=LOGGING)
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
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return None

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)
            return

        text = resp.text

        # 响应内容转为selector选择器
        selector = self.server.getSelector(resp=text)

        # 图片url存储列表
        img_list = []

        # 获取标题
        save_data['title'] = self.server.getTitle(select=selector)
        # 获取标识
        save_data['biaoShi'] = self.server.getBiaoShi(select=selector)
        # 存入图片列表
        if save_data['biaoShi']:
            img_list.append(save_data['biaoShi'])
        # 获取简介
        save_data['jianJie'] = self.server.getJianJie(html=text)

        # 存储图片
        if img_list:
            for img in img_list:
                img_dict = {}
                img_dict['bizTitle'] = save_data['title']
                img_dict['relEsse'] = self.server.guanLianJiGou(url=url, sha=sha)
                img_dict['relPics'] = {}
                img_url = img
                # # 存储图片种子
                # self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
                # 获取图片响应
                media_resp = self.__getResp(func=self.download_middleware.getResp,
                                            url=img_url,
                                            mode='GET')
                if not media_resp:
                    LOGGING.error('图片响应失败, url: {}'.format(img_url))
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)
                    return

                img_content = media_resp.content
                # 存储图片
                self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')

        # ===================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '机构'
        # 生成clazz ——层级关系
        save_data['clazz'] = '机构_标准职能机构'
        # 生成es ——栏目名称
        save_data['es'] = '标准'
        # 生成ws ——网站名称
        save_data['ws'] = 'mystandards'
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
        # self.dao.deleteTask(table=config.MYSQL_INSTITUTE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_INSTITUTE, count=20, lockname=config.REDIS_INSTITUTE_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for task in task_list:
                #     threadpool.apply_async(func=self.run, args=(task,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"url": "https://www.mystandards.biz/publisher/international-technical-standards-iso/"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
