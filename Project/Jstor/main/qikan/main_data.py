# -*-coding:utf-8-*-

'''

'''
import asyncio
import aiohttp
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
LOGNAME = 'Jstor_期刊_data'  # LOG名
NAME = 'Jstor_期刊_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.DownloaderMiddleware(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_QiKanServer(logging=LOGGING)
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
        self.index_url = 'https://www.jstor.org/'
        self.session = None

    async def __getResp(self, url, method, session=None, data=None, cookies=None, referer=''):
        # 发现验证码，最多访问页面10次
        for i in range(10):
            resp = await self.download_middleware.getResp(url=url, method=method, session=session, data=data, cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.get('text'):
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    # 模板
    async def template(self, save_data, select, html):
        # 获取标题
        save_data['title'] = self.server.getTitle(select)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(html)
        # 获取覆盖范围
        save_data['fuGaiFanWei'] = self.server.getFuGaiFanWei(select)
        # 获取国际标准刊号
        save_data['ISSN'] = self.server.getIssn(select)
        # 获取EISSN
        save_data['EISSN'] = self.server.getEissn(select)
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getXueKeLeiBie(select)
        # 获取出版社
        save_data['chuBanShe'] = self.server.getChuBanShe(select)


    async def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        # print(task_data)

        url = task_data['url']
        sha = task_data['sha']

        # 获取页面响应
        resp = await self.__getResp(session=self.session,
                                    url=url,
                                    method='GET')
        if not resp:
            LOGGING.error('页面响应获取失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
            return

        response = resp.get('text')
        # print(response)

        # 转为selector选择器
        selector = self.server.getSelector(response)

        # 获取字段值
        await self.template(save_data=save_data, select=selector, html=response)

        # =========================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '期刊'
        # 生成ws ——目标网站
        save_data['ws'] = 'JSTOR'
        # 生成clazz ——层级关系
        save_data['clazz'] = '期刊'
        # 生成es ——栏目名称
        save_data['es'] = 'Journals'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 返回sha为删除任务做准备
        return sha

    async def run(self, task):
        # 创建数据存储字典
        save_data = {}

        # 获取字段值存入字典并返回sha
        sha = await self.handle(task=task, save_data=save_data)

        # 保存数据到Hbase
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        self.dao.saveDataToHbase(data=save_data)

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_MAGAZINE, sha=sha)

    async def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_MAGAZINE, count=10, lockname=config.REDIS_MAGAZINE_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # 创建会话
                # conn = aiohttp.TCPConnector()
                self.session = aiohttp.ClientSession()
                # 请求首页，保持会话（cookies一致）
                await self.__getResp(session=self.session,
                               url=self.index_url,
                               method='GET')

                # 创建一个任务盒子tasks
                tasks = []
                for task in task_list:
                    s = asyncio.ensure_future(self.run(task))
                    tasks.append(s)

                await asyncio.gather(*tasks)

                await self.session.close()

                # # 获取cookie
                # self.cookie_dict = self.download_middleware.create_cookie()
                # # cookie创建失败，重新创建
                # if not self.cookie_dict:
                #     continue
                # # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])
                #
                # # 创建gevent协程
                # g_list = []
                # for task in task_list:
                #     s = gevent.spawn(self.run, task)
                #     g_list.append(s)
                # gevent.joinall(g_list)

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


async def process_start():
    main = SpiderMain()
    try:
        await main.start()
        # main.run(task='{"url": "https://www.jstor.org/journal/oceanography", "sha": "70de09416305f41f2ae5c0195edc9602856a9e4d", "ss": "期刊"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_start())
    loop.close()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
