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
from Project.YuBoBaoGao.middleware import download_middleware
from Project.YuBoBaoGao.service import service
from Project.YuBoBaoGao.dao import dao
from Project.YuBoBaoGao import config

log_file_dir = 'YuBo'  # LOG日志存放路径
LOGNAME = '<宇博_报告_data>'  # LOG名
NAME = '宇博_报告_data'  # 爬虫名
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

    def __getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(10):
            resp = self.download_middleware.getResp(url=url,
                                                    mode=mode,
                                                    s=s,
                                                    data=data,
                                                    cookies=cookies,
                                                    referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 200:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            return None

    # 获取价格实体字段
    def price(self, resp, title, url, sha):
        # 公告数据存储字典
        price_data = {}

        # 获取标题
        price_data['title'] = title
        # 获取商品价格
        price_data['shangPinJiaGe'] = self.server.getShangPinJiaGe(resp)
        # 关联报告
        price_data['guanLianBaoGao'] = self.server.guanLianBaoGao(url=url, sha=sha)

        # ===================公共字段
        # url
        price_data['url'] = url
        # 生成key
        price_data['key'] = url
        # 生成sha
        price_data['sha'] = sha
        # 生成ss ——实体
        price_data['ss'] = '价格'
        # 生成es ——栏目名称
        price_data['es'] = '行业研究报告'
        # 生成ws ——目标网站
        price_data['ws'] = '宇博报告大厅'
        # 生成clazz ——层级关系
        price_data['clazz'] = '价格'
        # 生成biz ——项目
        price_data['biz'] = '文献大数据'
        # 生成ref
        price_data['ref'] = ''

        # 保存数据到Hbase
        sto = self.dao.saveDataToHbase(data=price_data)

        if sto:
            LOGGING.info('价格数据存储成功, sha: {}'.format(sha))

        else:
            LOGGING.error('价格数据存储失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_REPORT, sha=sha)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        hangYe = task_data['s_hangYe']
        leiXing = task_data['s_leiXing']

        # 获取页面响应
        resp = self.__getResp(url=url, mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_REPORT, sha=sha)
            return

        resp.encoding = resp.apparent_encoding
        response = resp.text
        # with open ('profile.html', 'w', encoding='utf-8') as f:
        #     f.write(response)
        # return

        # 获取标题
        save_data['title'] = self.server.getTitle(response)
        # 获取来源网站
        save_data['laiYuanWangZhan'] = self.server.getLaiYuanWangZhan(response)
        # 获取组图
        save_data['zuTu'] = self.server.getZuTu(response)
        # 保存图片
        if save_data['zuTu']:
            img_dict = {}
            img_dict['bizTitle'] = save_data['title']
            img_dict['relEsse'] = self.server.guanLianBaoGao(url=url, sha=sha)
            img_dict['relPics'] = {}
            img_url = save_data['zuTu']
            sha1 = hashlib.sha1(img_url.encode('utf-8')).hexdigest()
            # # 存储图片种子
            # self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
            # 获取图片响应
            media_resp = self.__getResp(url=img_url, mode='GET')
            if not media_resp:
                LOGGING.error('图片响应失败, url: {}'.format(img_url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_REPORT, sha=sha)
                return

            img_content = media_resp.content
            # 存储图片
            sto = self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')
            if sto:
                LOGGING.info('图片存储成功, sha: {}'.format(sha1))
            else:
                LOGGING.error('图片存储失败, url: {}'.format(url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_REPORT, sha=sha)
                return

        # 获取编号
        save_data['bianHao'] = self.server.getField(response, '报告编号')
        # 获取发布时间
        faBuShiJian = self.server.getField(response, '最新修订')
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
        # 获取标签
        save_data['biaoQian'] = self.server.getGuanJianZi(response)
        # 获取文件格式
        save_data['wenJianGeShi'] = self.server.getField(response, '报告格式')
        # 获取导读
        save_data['daoDu'] = self.server.getDaoDu(response)
        # 获取目录
        save_data['muLu'] = self.server.getMuLu(response)
        # 获取行业
        save_data['hangYe'] = hangYe
        # 获取类型
        save_data['leiXing'] = leiXing

        # 获取价格实体
        jiaGe = self.server.getJiaGe(response)
        if jiaGe:
            self.price(resp=response, title=save_data['title'], url=url, sha=sha)

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '报告'
        # 生成es ——栏目名称
        save_data['es'] = '行业研究报告'
        # 生成ws ——目标网站
        save_data['ws'] = '宇博报告大厅'
        # 生成clazz ——层级关系
        save_data['clazz'] = '报告_调研报告'
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
        # 存储数据
        success = self.dao.saveDataToHbase(data=save_data)
        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_REPORT, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_REPORT, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_YUBO_REPORT, count=20, lockname=config.REDIS_YUBO_REPORT_LOCK)
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
        # main.run(task='{"url": "http://www.chinabgao.com/report/4261297.html", "s_hangYe": "石油_成品油", "s_leiXing": "市场分析"}')
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
