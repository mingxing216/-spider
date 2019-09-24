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
import asyncio
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Normadoc.middleware import download_middleware
from Project.Normadoc.service import service
from Project.Normadoc.dao import dao
from Project.Normadoc import config

log_file_dir = 'Normadoc'  # LOG日志存放路径
LOGNAME = 'Normadoc_标准_data'  # LOG名
NAME = 'Normadoc_标准_data'  # 爬虫名
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
        # 发现验证码，最多访问页面10次
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

    # 获取价格实体字段
    def price(self, select, title, url, sha):
        # 价格数据存储字典
        price_data = {}
        # 标题
        price_data['title'] = title
        # 商品价格
        price_data['shangPinJiaGe'] = self.server.getPrice(select=select)
        # 关联标准
        price_data['guanLianBiaoZhun'] = self.server.guanLianBiaoZhun(url=url, sha=sha)
        # ===================公共字段
        # url
        price_data['url'] = url
        # 生成key
        price_data['key'] = url
        # 生成sha
        price_data['sha'] = sha
        # 生成ss ——实体
        price_data['ss'] = '价格'
        # 生成clazz ——层级关系
        price_data['clazz'] = '价格'
        # 生成es ——栏目名称
        price_data['es'] = '标准'
        # 生成ws ——目标网站
        price_data['ws'] = 'normadoc'
        # 生成biz ——项目
        price_data['biz'] = '文献大数据'
        # 生成ref
        price_data['ref'] = ''

        # 保存数据到Hbase
        self.dao.saveDataToHbase(data=price_data)

    # 获取标准实体字段
    def standard(self, save_data, select, html, url, sha):
        # 获取标准编号
        save_data['biaoZhunBianHao'] = self.server.getBiaoZhunBianHao(select)
        # 获取标题
        save_data['title'] = self.server.getTitle(select)
        # 获取标准状态
        save_data['biaoZhunZhuangTai'] = self.server.getZhuangTai(select)
        # 获取描述
        save_data['miaoShu'] = self.server.getMiaoShu(html)
        # 获取作者信息
        save_data['zuoZheXinXi'] = self.server.getField(select, 'Author')
        # 获取标准发布组织
        save_data['biaoZhunFaBuZuZhi'] = self.server.getField(select, 'Editor')
        # 获取标准类型
        save_data['biaoZhunLeiXing'] = self.server.getField(select, 'Document type')
        # 获取版本
        save_data['banBen'] = self.server.getField(select, 'Edition')
        # 获取国际标准分类号
        save_data['guoJiBiaoZhunFenLeiHao'] = self.server.getFenLeiHao(select)
        # 获取页数
        save_data['yeShu'] = self.server.getField(select, 'Number of pages')
        # 获取被代替标准
        save_data['beiDaiTiBiaoZhun'] = self.server.getBiaoZhun(select, 'Replace')
        # 获取引用标准
        save_data['yinYongBiaoZhun'] = self.server.getBiaoZhun(select, 'Cross references')
        # 获取发布日期
        save_data['faBuRiQi'] = self.server.getField(select, 'Year')
        # 获取国别
        save_data['guoBie'] = self.server.getField(select, 'Country')
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(select)
        # 获取废止日期
        save_data['feiZhiRiQi'] = self.server.getRiQi(select, 'expiration_de_validite')
        # 获取修订标准
        save_data['xiuDingBiaoZhun'] = self.server.getXiuDing(select, 'Modified by')
        # 获取被修订标准
        save_data['beiXiuDingBiaoZhun'] = self.server.getXiuDing(select, 'Modify')
        # 获取确认日期
        save_data['queRenRiQi'] = self.server.getRiQi(select, 'Confirmation date')

        # 获取价格实体
        self.price(select=select, title=save_data['title'], url=url, sha=sha)


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
            self.dao.deleteLogicTask(table=config.MYSQL_STANDARD, sha=sha)
            return

        response = resp.text

        # 转为selector选择器
        selector = self.server.getSelector(response)
        # 获取标准实体字段
        self.standard(save_data=save_data, select=selector, html=response, url=url, sha=sha)

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
        save_data['ws'] = 'normadoc'
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
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        self.dao.saveDataToHbase(data=save_data)
        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_STANDARD, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_STANDARD, count=10, lockname=config.REDIS_STANDARD_LOCK)
            # print(task_list)
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
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"url": "http://www.normadoc.com/english/bs-en-60730-2-5-2002-a2-2010-1768174.html"}')
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
