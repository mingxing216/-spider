# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import copy
import traceback
import hashlib
import json
import datetime
import asyncio
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import gevent
from gevent import monkey
monkey.patch_all()

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.SAIglobal.middleware import download_middleware
from Project.SAIglobal.service import service
from Project.SAIglobal.dao import dao
from Project.SAIglobal import config

log_file_dir = 'SAIglobal'  # LOG日志存放路径
LOGNAME = 'SAIglobal_标准_data'  # LOG名
NAME = 'SAIglobal_标准_data'  # 爬虫名
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
        self.xml_url = 'https://infostore.saiglobal.com/Components/Service/HomePageService.asmx/GetProductVariationDetail'

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
        # 获取价格接口访问参数
        names = self.server.getName(select)
        if names:
            # 价格数据存储字典
            price_data = {}
            # 标题
            price_data['title'] = title
            # 价格
            price_data['shangPinJiaGe'] = []
            for name in names:
                payloadData = {
                    'currencyMnemonic': 'AUD',
                    'languageID': 0,
                    'variationSKU': name[0]
                }
                # 原网页post请求参数为Request Payload,而非Form Data。所以参数变为json字符串,同时请求头需要加一行
                jsonData = json.dumps(payloadData)

                respon = self.__getResp(func=self.download_middleware.getResp,
                                        url=self.xml_url,
                                        mode='POST',
                                        data=jsonData)
                if not respon:
                    LOGGING.error('接口响应失败, url: {}'.format(self.xml_url))
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_STANTARD, sha=sha)
                    return "中断"
                # 响应结果变为json对象
                json_dict = json.loads(respon.text)
                price_dict = {}
                price_dict['PRODUCT FORMAT'] = name[1]
                price_dict['Price'] = self.server.getPrice(json=json_dict)
                price_data['shangPinJiaGe'].append(price_dict)
            # 关联标准
            price_data['guanLianBiaoZhun'] = self.server.guanLianBiaoZhun(url)
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
            price_data['ws'] = 'SAI GLOBAL'
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
        # 获取摘要
        save_data['zhaiYao'] = self.server.getHtmlField(html, 'Abstract')
        # 获取描述
        save_data['miaoShu'] = self.server.getHtmlField(html, 'Scope')
        # 获取标准类型
        save_data['biaoZhunLeiXing'] = self.server.getField(select, 'Document Type')
        # 获取标准状态
        save_data['biaoZhunZhaungTai'] = self.server.getField(select, 'Status')
        # 获取标准发布组织
        save_data['biaoZhunFaBuZuZhi'] = self.server.getFaBuZuZhi(select)
        # 获取被代替标准
        save_data['beiDaiTiBiaoZhun'] = self.server.getXuLieField(select, 'Supersedes')
        # 获取代替标准
        save_data['daiTiBiaoZhun'] = self.server.getXuLieField(select, 'Superseded By')
        # 获取引用标准
        save_data['yinYongBiaoZhun'] = self.server.getYinYongBiaoZhun(select)
        # 获取国际标准类别
        save_data['guoJiBiaoZhunLeiBie'] = self.server.getGuoJiBiaoZhunLeiBie(html)
        # 获取等效标准
        save_data['dengXiaoBiaoZhun'] = self.server.getDengXiaoBiaoZhun(select)
        # 获取关联文档
        save_data['guanLianWenDang'] = self.server.guanLianWenDang(select)
        if save_data['guanLianWenDang']:
            # 深拷贝关联文档字典，目的为了修改拷贝的内容后，原文档字典不变
            document = copy.deepcopy(save_data['guanLianWenDang'])
            document['parentUrl'] = url
            document['title'] = save_data['title']
            # 存储文档种子
            self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=document, ws='SAI GLOBAL', es='标准')

        # 获取variationSKU参数
        sku = self.server.getSku(select)
        if sku:
            payloadData = {
                'currencyMnemonic': 'AUD',
                'languageID': 0,
                'variationSKU': sku
            }
            # post请求参数变为json字符串
            jsonData = json.dumps(payloadData)

            respon = self.__getResp(func=self.download_middleware.getResp,
                                    url=self.xml_url,
                                    mode='POST',
                                    data=jsonData)
            if not respon:
                LOGGING.error('接口响应失败, url: {}'.format(self.xml_url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_STANTARD, sha=sha)
                return "中断"
            # 响应结果变为json对象
            json_dict = json.loads(respon.text)

            # 获取发布日期
            save_data['faBuRiQi'] = self.server.getFaBuRiQi(json=json_dict)
            # 获取页数
            save_data['yeShu'] = self.server.getYeShu(json=json_dict)
            # 获取国际标准书号
            save_data['ISBN'] = self.server.getIsbn(json=json_dict)
        else:
            # 获取发布日期
            save_data['faBuRiQi'] = ""
            # 获取页数
            save_data['yeShu'] = ""
            # 获取国际标准书号
            save_data['ISBN'] = ""

        # ============价格实体
        return self.price(select, save_data['title'], url, sha)

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
            self.dao.deleteLogicTask(table=config.MYSQL_STANTARD, sha=sha)
            return

        response = resp.text

        # 转为selector选择器
        selector = self.server.getSelector(response)
        # =======获取标准实体，并返回结果
        result = self.standard(save_data=save_data, select=selector, html=response, url=url, sha=sha)
        # 如果返回结果为"中断"，该种子所抓数据不存储
        if result:
            return
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
        save_data['ws'] = 'SAI GLOBAL'
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
        self.dao.deleteTask(table=config.MYSQL_STANTARD, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_STANTARD, count=20, lockname=config.REDIS_STANTARD_LOCK)
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
        # main.run(task='{"url": "https://infostore.saiglobal.com/en-au/Standards/AS-2560-1-2002-124146_SAIG_AS_AS_261011/"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    # po = Pool(1)
    # for i in range(1):
    #     po.apply_async(func=process_start)

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
