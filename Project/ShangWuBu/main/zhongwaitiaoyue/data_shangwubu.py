# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import traceback
import hashlib
import requests
from datetime import datetime
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ShangWuBu.middleware import download_middleware
from Project.ShangWuBu.service import service
from Project.ShangWuBu.dao import dao
from Project.ShangWuBu import config

log_file_dir = 'ShangWuBu'  # LOG日志存放路径
LOGNAME = '<商务部_中外条约_data>'  # LOG名
NAME = '商务部_中外条约_data'  # 爬虫名
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
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        qianDingShiJian = task_data['nianfen']
        es = task_data['es']
        clazz = task_data['clazz']

        # 获取页面响应
        resp = self.__getResp(url=url, method='GET')
        if not resp:
            LOGGING.error('正文页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_LAW, sha=sha)
            return

        resp.encoding = resp.apparent_encoding
        content = resp.text
        # with open ('profile.html', 'w', encoding='utf-8') as f:
        #     f.write(content)
        # return

        # 获取标题
        save_data['title'] = self.server.getTitle(content)
        # 获取正文
        save_data['zhengWen'] = self.server.getContent(content)
        # 获取基本信息url
        info_url = self.server.getInfoUrl(content)

        info_text = ''
        if info_url:
            # 获取页面响应
            info_resp = self.__getResp(url=info_url, method='GET')
            if not info_resp:
                LOGGING.error('基本信息页面响应失败, url: {}'.format(info_url))
                # 逻辑删除任务
                self.dao.delete_logic_task_from_mysql(table=config.MYSQL_LAW, sha=sha)
                return

            info_resp.encoding = info_resp.apparent_encoding
            info_text = info_resp.text

        # 获取国家与国际组织
        save_data['guoJiaYuGuoJiZuZhi'] = self.server.getMoreField(info_text, '国家与国际组织')
        # 获取签订日期
        qianDingRiQi = self.server.getField(info_text, '签订日期')
        if qianDingRiQi:
            try:
                if '-' in qianDingRiQi:
                    save_data['qianDingRiQi'] = str(datetime.strptime(qianDingRiQi, '%Y-%m-%d'))
                else:
                    save_data['qianDingRiQi'] = str(datetime.strptime(qianDingRiQi, '%Y年%m月%d日'))
            except:
                save_data['qianDingRiQi'] = qianDingRiQi
        else:
            save_data['qianDingRiQi'] = ""
        # 获取条约种类
        save_data['tiaoYueZhongLei'] = self.server.getField(info_text, '条约种类')
        # 获取批准部门
        save_data['piZhunBuMen'] = self.server.getField(info_text, '批准部门')
        # 获取类别
        save_data['leiBie'] = self.server.getMoreField(info_text, '条约话题')
        # 获取时效状态
        save_data['shiXiaoZhuangTai'] = self.server.getField(info_text, '时效状态')
        # 获取签订地点
        save_data['qianDingDiDian'] = self.server.getField(info_text, '签订地点')
        # 获取签订时间
        save_data['qianDingShiJian'] = qianDingShiJian

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '法律'
        # 生成es ——栏目名称
        save_data['es'] = es
        # 生成ws ——目标网站
        save_data['ws'] = '中华人民共和国商务部'
        # 生成clazz ——层级关系
        save_data['clazz'] = clazz
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_法律'
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
        # 存储数据
        success = self.dao.save_data_to_hbase(data=save_data)
        if success:
            # 删除任务
            self.dao.delete_task_from_mysql(table=config.MYSQL_LAW, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_LAW, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.get_task_from_redis(key=config.REDIS_TIAOYUE_LAW, count=10, lockname=config.REDIS_TIAOYUE_LAW_LOCK)
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
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
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
        # main.run(task='{"url": "http://policy.mofcom.gov.cn/pact/pactContent.shtml?id=2664", "nianfen": {"Y": "2010及更早"}, "es": "公约", "clazz": "法律法规_国际条约_公约"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
