# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import copy
import traceback
import hashlib
import datetime
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Jstor.middleware import download_middleware
from Project.Jstor.service import service
from Project.Jstor.dao import dao
from Project.Jstor import config

log_file_dir = 'Jstor'  # LOG日志存放路径
LOGNAME = 'Jstor_图片_data'  # LOG名
NAME = 'Jstor_图片_data'  # 爬虫名
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
        self.server = service.QiKanLunWen_LunWenServer(logging=LOGGING)
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

    def run(self, task):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        print(task_data)
        # 创建数据存储字典
        save_data = {}
        save_data['bizTitle'] = task_data['bizTitle']
        save_data['relEsse'] = task_data['relEsse']
        save_data['relPics'] = task_data['relPics']

        img_url = task_data['url']
        sha = hashlib.sha1(img_url.encode('utf-8')).hexdigest()

        # # 获取cookie
        # self.cookie_dict = self.download_middleware.create_cookie()
        # if not self.cookie_dict:
        #     # 逻辑删除任务
        #     self.dao.deleteLogicTask(table=config.MYSQL_IMG, sha=sha)
        #     return
        # 访问图片url，获取响应
        media_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=img_url,
                                    mode='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_IMG, sha=sha)
            return
        img_content = media_resp.text

        # 存储图片
        self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=save_data, type='image')

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_IMG, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_IMG, count=10, lockname=config.REDIS_IMG_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

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
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task="{\"bizTitle\": \"Back Matter\", \"relEsse\": {\"url\": \"https://www.jstor.org/stable/40693082?Search=yes&resultItemClick=true&&searchUri=%2Fdfr%2Fresults%3Fpagemark%3DcGFnZU1hcms9Mg%253D%253D%26amp%3BsearchType%3DfacetSearch%26amp%3Bcty_journal_facet%3Dam91cm5hbA%253D%253D%26amp%3Bsd%3D1912%26amp%3Bed%3D1913%26amp%3Bacc%3Ddfr%26amp%3Bdisc_astronomy-discipline_facet%3DYXN0cm9ub215LWRpc2NpcGxpbmU%253D&ab_segments=0%2Fdefault-2%2Fcontrol\", \"sha\": \"00a3cf208165a551473f065c2e43f8b6f90a42b4\", \"ss\": \"\xe8\xae\xba\xe6\x96\x87\"}, \"url\": \"https://www.jstor.org/stable/get_image/40693082?path=czM6Ly9zZXF1b2lhLWNlZGFyL2NpZC1wcm9kLTEvOTUwNzcxYzEvODQwMC8zYjc4LzkwMjEvMTE0NDM5YjFjYjNlL2k0MDAzMDQzMy80MDY5MzA4Mi9ncmFwaGljL3BhZ2VzL2R0Yy42Ny50aWYuZ2lm\"}")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()

    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)

    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
