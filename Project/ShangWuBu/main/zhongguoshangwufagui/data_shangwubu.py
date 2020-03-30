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
LOGNAME = '<商务部_中国商务法规_data>'  # LOG名
NAME = '商务部_中国商务法规_data'  # 爬虫名
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
        faBuNianFen = task_data['nianfen']
        es = task_data['es']
        clazz = task_data['clazz']

        # 获取页面响应
        resp = self.__getResp(url=url, method='GET')
        if not resp:
            LOGGING.error('正文页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_LAW, sha=sha)
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
                self.dao.deleteLogicTask(table=config.MYSQL_LAW, sha=sha)
                return

            info_resp.encoding = info_resp.apparent_encoding
            info_text = info_resp.text

        # 获取发布单位
        save_data['faBuDanWei'] = self.server.getField(info_text, '发布部门')
        # 获取效力级别
        save_data['xiaoLiJiBie'] = self.server.getField(info_text, '效力级别')
        # 获取发布时间
        faBuShiJian = self.server.getField(info_text, '发布日期')
        if faBuShiJian:
            try:
                if '-' in faBuShiJian:
                    save_data['faBuShiJian'] = str(datetime.strptime(faBuShiJian, '%Y-%m-%d'))
                else:
                    save_data['faBuShiJian'] = str(datetime.strptime(faBuShiJian, '%Y年%m月%d日'))
            except:
                save_data['faBuShiJian'] = faBuShiJian
        else:
            save_data['faBuShiJian'] = ""
        # 获取类别
        save_data['leiBie'] = self.server.getMoreField(info_text, '法律话题')
        # 获取发布文号
        save_data['faBuWenHao'] = self.server.getField(info_text, '发布文号')
        # 获取时效状态
        save_data['shiXiaoZhuangTai'] = self.server.getField(info_text, '时效状态')
        # 获取生效日期
        shengXiaoRiQi = self.server.getField(info_text, '实施日期')
        if shengXiaoRiQi:
            try:
                if '-' in shengXiaoRiQi:
                    save_data['shengXiaoRiQi'] = str(datetime.strptime(shengXiaoRiQi, '%Y-%m-%d'))
                else:
                    save_data['shengXiaoRiQi'] = str(datetime.strptime(shengXiaoRiQi, '%Y年%m月%d日'))
            except:
                save_data['shengXiaoRiQi'] = shengXiaoRiQi
        else:
            save_data['shengXiaoRiQi'] = ""
        # 获取产业领域
        save_data['chanYeLingYu'] = self.server.getMoreField(info_text, '产业领域')
        # 获取发布年份
        save_data['faBuNianFen'] = faBuNianFen

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
        success = self.dao.saveDataToHbase(data=save_data)
        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_LAW, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_LAW, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_FAGUI_LAW, count=10, lockname=config.REDIS_FAGUI_LAW_LOCK)
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
        # main.run(task='{"url": "http://policy.mofcom.gov.cn/claw/clawContent.shtml?id=63351", "nianfen": {"Y": "2017"}, "es": "法律", "clazz": "法律法规_中国内地法律法规_中央法律法规_宪法法律"}')
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
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
