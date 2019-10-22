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
from Project.Nasa.middleware import download_middleware
from Project.Nasa.service import service
from Project.Nasa.dao import dao
from Project.Nasa import config

log_file_dir = 'Nasa'  # LOG日志存放路径
LOGNAME = 'Nasa_期刊_data'  # LOG名
NAME = 'Nasa_期刊_data'  # 爬虫名
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

    # 模板
    def template(self, save_data, content):
        # 获取标题
        save_data['title'] = self.server.getValue(content, 'displayTitle')
        # 获取影响因子
        save_data['yingXiangYinZi'] = self.server.getValue(content, 'impactFactor')
        # 获取特征因子
        save_data['teZhengYinZi'] = self.server.getValue(content, 'eigenFactorScore')
        # 获取论文影响分值
        save_data['lunWenYingXiangFenZhi'] = self.server.getValue(content, 'articleInfluenceMetricScore')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(content)
        # 获取频率
        save_data['pinLv'] = self.server.getValue(content, 'frequency')
        # 获取详情
        details = self.server.getDetails(content)
        # 将详情转为选择器
        selector = self.server.getSelector(resp=details)
        # 获取国际标准刊号
        save_data['ISSN'] = self.server.getIssn(selector)
        # 获取出版社
        save_data['chuBanShe'] = self.server.getXuLie(selector, 'Published')
        # 获取出版信息
        save_data['chuBanXinXi'] = self.server.getXuLie(selector, 'Information')
        # 获取联系方式
        save_data['lianXiFangShi'] = self.server.getLianXiFangShi(content)
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getXueKeLeiBie(content)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        qiZhiShiJian = task_data['qiZhiShiJian']
        number = task_data['number']

        # 期刊详情页接口url
        journal_url = 'https://ieeexplore.ieee.org/rest/publication/home/metadata?pubid=' + str(number)

        # 获取页面响应
        journal_resp = self.__getResp(func=self.download_middleware.getResp,
                              url=journal_url,
                              mode='GET')
        if not journal_resp:
            LOGGING.error('页面响应失败, url: {}'.format(journal_url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
            return

        journal_json = journal_resp.json()
        # print(response)

        # 获取字段值
        self.template(save_data=save_data, content=journal_json)

        # =========================公共字段
        # 获取起止时间
        save_data['qiZhiShiJian'] = qiZhiShiJian
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '期刊'
        # 生成es ——栏目名称
        save_data['es'] = '期刊'
        # 生成ws ——目标网站
        save_data['ws'] = '电气和电子工程师协会'
        # 生成clazz ——层级关系
        save_data['clazz'] = '期刊'
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
        self.dao.deleteTask(table=config.MYSQL_MAGAZINE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_MAGAZINE, count=10, lockname=config.REDIS_MAGAZINE_LOCK)
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
        # main.run(task='{"number": "10", "url": "https://ieeexplore.ieee.org/xpl/aboutJournal.jsp?punumber=10", "qiZhiShiJian": "1990 - Present"}')
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
