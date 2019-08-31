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
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import gevent
from gevent import monkey
monkey.patch_all()

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Mystandards.middleware import download_middleware
from Project.Mystandards.service import service
from Project.Mystandards.dao import dao
from Project.Mystandards import config

log_file_dir = 'Mystandards'  # LOG日志存放路径
LOGNAME = 'Mystandards_文档_data'  # LOG名
NAME = 'Mystandards_文档_data'  # 爬虫名
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
        sha = task_data['sha']
        parentUrl = task_data['parentUrl']
        title = task_data['title']
        # 获取标题
        save_data['title'] = title
        # 获取URL
        save_data['xiaZaiLianJie'] = url
        # 获取格式
        save_data['geShi'] = ""
        # 获取大小
        save_data['daXiao'] = ""
        # 获取标签
        save_data['biaoQian'] = ""
        # 获取来源网站
        save_data['laiYuanWangZhan'] = ""
        # 获取关联标准
        e = {}
        e['url'] = parentUrl
        e['sha'] = hashlib.sha1(e['url'].encode('utf-8')).hexdigest()
        e['ss'] = '标准'
        save_data['guanLianBiaoZhun'] = e
        # =========================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '文档'
        # 生成clazz ——层级关系
        save_data['clazz'] = '文档_标准文档'
        # 生成es ——栏目名称
        save_data['es'] = '标准'
        # 生成ws ——目标网站
        save_data['ws'] = 'SAI GLOBAL'
        # 生成biz ——项目
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
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        self.dao.saveDataToHbase(data=save_data)
        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_DOCUMENT, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_DOCUMENT, count=32, lockname=config.REDIS_DOCUMENT_LOCK)
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
                time.sleep(3)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"url": "https://infostore.saiglobal.com/preview/480232435226.pdf?sku=1154349_SAIG_AS_AS_2740572", "sha": "e31a210696e020af8f3ce2e6715765cc7bd6600e", "ss": "文档", "parentUrl": "https://infostore.saiglobal.com/en-au/Standards/AS-ISO-IEC-25063-2019-1154349_SAIG_AS_AS_2740572/", "title": "Systems and software engineering - Systems and software product Quality Requirements and Evaluation (SQuaRE) - Common Industry Format (CIF) for usability: Context of use description"}')
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
