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
import json
import datetime
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Ieee.middleware import download_middleware
from Project.Ieee.service import service
from Project.Ieee.dao import dao
from Project.Ieee import config

log_file_dir = 'Ieee'  # LOG日志存放路径
LOGNAME = 'Ieee_会议_data'  # LOG名
NAME = 'Ieee_会议_data'  # 爬虫名
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
        self.server = service.HuiYiLunWen_LunWenServer(logging=LOGGING)
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

    # 模板
    def template(self, save_data, content, number, sha):
        # 获取标题
        save_data['title'] = self.server.getTitle(content)
        # 获取举办时间
        save_data['juBanShiJian'] = self.server.getJuBanShiJian(content)
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getXueKeLeiBie(content)

        # 获取issueNumber参数
        try:
            isNumber = content['currentIssue']['issueNumber']
        except Exception:
            isNumber = ''
        # 获取论文列表页
        if isNumber:
            catalog_url = 'https://ieeexplore.ieee.org/rest/search/pub/' + str(number) + '/issue/' + str(isNumber) + '/toc'
            # 访问会议论文列表页接口，获取响应
            payloadData = {
                'isnumber': isNumber,
                'punumber': number
            }

            jsonData = json.dumps(payloadData)

            catalog_resp = self.__getResp(func=self.download_middleware.getResp,
                                          url=catalog_url,
                                          mode='POST',
                                          data=jsonData)
            if not catalog_resp:
                LOGGING.error('页面响应失败, url: {}'.format(catalog_url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_ACTIVITY, sha=sha)
                return '中断'

            catalog_json = catalog_resp.json()

            # 获取所在地_内容
            save_data['suoZaiDiNeiRong'] = self.server.getSuoZaiDi(content=catalog_json)
        else:
            save_data['suoZaiDiNeiRong'] = ""

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        number = task_data['number']

        # 会议详情页接口url
        conference_url = 'https://ieeexplore.ieee.org/rest/publication/home/metadata?pubid=' + str(number)
        # 访问会议详情页
        conference_resp = self.__getResp(func=self.download_middleware.getResp,
                                      url=conference_url,
                                      mode='GET')
        if not conference_resp:
            LOGGING.error('页面响应失败, url: {}'.format(conference_url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_ACTIVITY, sha=sha)
            return

        conference_json = conference_resp.json()

        # 获取字段值
        results = self.template(save_data=save_data, content=conference_json, number=number, sha=sha)
        # 如果返回结果为"中断"，该种子所抓数据不存储
        if results:
            return

        # =========================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '活动'
        # 生成es ——栏目名称
        save_data['es'] = '会议'
        # 生成clazz ——层级关系
        save_data['clazz'] = '活动_会议'
        # 生成ws ——目标网站
        save_data['ws'] = '电气和电子工程师协会'
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
        self.dao.deleteTask(table=config.MYSQL_ACTIVITY, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_ACTIVITY, count=10, lockname=config.REDIS_ACTIVITY_LOCK)
            # print(task_list)
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
        # main.run(task='{"number": "5171", "url": "https://ieeexplore.ieee.org/xpl/conhome/5171/proceeding"}')
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
