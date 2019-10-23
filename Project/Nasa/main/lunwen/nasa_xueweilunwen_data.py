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
from datetime import datetime
import requests
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Nasa.middleware import download_middleware
from Project.Nasa.service import service
from Project.Nasa.dao import dao
from Project.Nasa import config

log_file_dir = 'Nasa'  # LOG日志存放路径
LOGNAME = 'Nasa_学位论文_data'  # LOG名
NAME = 'Nasa_学位论文_data'  # 爬虫名
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
        self.server = service.LunWen_LunWenServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.cookie_dict = ''

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

    # 作者实体
    def zuoZhe(self, selector, url, sha, es):
        try:
            authors = selector.xpath("//td[@id='colTitle' and contains(text(), 'Author')]/following-sibling::td[1]//table/tr")
            for author in authors:
                author_dict = {}
                # 标题
                author_dict['title'] = self.server.getAuthorTitle(content=author)
                # 所在单位
                author_dict['suoZaiDanWei'] = self.server.getDanWei(content=author)
                # 缩写_ORCID
                author_dict['ORCID'] = self.server.getORCID(content=author)
                # 获取sha
                id = url + '#' + author_dict['title'] + '#' + author_dict['suoZaiDanWei']
                sha1 = hashlib.sha1(id.encode('utf-8')).hexdigest()

                # ======================== 公共字段
                # url
                author_dict['url'] = url
                # 生成key
                author_dict['key'] = url
                # 生成sha
                author_dict['sha'] = sha1
                # 生成ss ——实体
                author_dict['ss'] = '人物'
                # 生成es ——栏目名称
                author_dict['es'] = es
                # 生成ws ——目标网站
                author_dict['ws'] = '美国宇航局'
                # 生成clazz ——层级关系
                author_dict['clazz'] = '人物_论文作者'
                # 生成biz ——项目
                author_dict['biz'] = '文献大数据'
                # 生成ref
                author_dict['ref'] = ''

                # 存储数据
                sto = self.dao.saveDataToHbase(data=author_dict)
                if not sto:
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                    LOGGING.error('作者数据存储失败, url: {}'.format(url))
        except Exception:
            pass

    # 论文实体
    def lunWen(self, save_data, selector, resp, url, sha, es):
        # 获取标题
        save_data['title'] = self.server.getTitle(selector)
        # 获取作者
        save_data['zuoZhe'] = self.server.getZuoZhe(selector)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(resp)
        # 获取时间
        shijian = self.server.getField(selector, 'Publication Date')
        if shijian:
            try:
                save_data['shiJian'] = str(datetime.strptime(shijian, "%B %d, %Y"))
            except:
                save_data['shiJian'] = shijian
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getMoreField(selector, 'Subject Category')
        # 获取报告_专利号
        save_data['baoGaoZhuanLiHao'] = self.server.getField(selector, 'Report/Patent Number')
        # 获取赞助商
        save_data['zanZhuShang'] = self.server.getMoreField(selector, 'Financial Sponsor')
        # 获取组织来源
        save_data['zuZhiLaiYuan'] = self.server.getMoreField(selector, 'Organization Source')
        # 获取描述
        save_data['miaoShu'] = self.server.getField(selector, 'Description')
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(selector)
        # 关联作者
        save_data['guanLianZuoZhe'] = self.server.guanLianZuoZhe(selector, url=url)
        # 获取作者实体字段值
        if save_data['guanLianZuoZhe']:
            return self.zuoZhe(selector, url=url, sha=sha, es=es)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        pdfUrl = task_data['pdfUrl']
        es = task_data['es']

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        response = resp.text
        # with open('profile.html', 'w') as f:
        #     f.write(response)
        # print(response)

        # 获取selector选择器
        selector = self.server.getSelector(response)

        result = self.lunWen(save_data=save_data, selector=selector, resp=response, url=url, sha=sha, es=es)
        if result:
            return

        # ===================公共字段
        if pdfUrl:
            # 获取下载链接
            save_data['xiaZaiLianJie'] = pdfUrl
            # 关联文档
            save_data['guanLianWenDang'] = self.server.guanLianWenDang(url=pdfUrl)
        else:
            # 获取下载链接
            save_data['xiaZaiLianJie'] = ""
            # 关联文档
            save_data['guanLianWenDang'] = {}
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成es ——栏目名称
        save_data['es'] = es
        # 生成ws ——目标网站
        save_data['ws'] = '美国宇航局'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_学位论文'
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
            self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_XUEWEI_PAPER, count=10, lockname=config.REDIS_XUEWEI_PAPER_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))
            print(task_list)

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
        # main.run(task='{"url": "https://ntrs.nasa.gov/search.jsp?R=20190002542&qs=N%3D4294946866%26No%3D1190", "pdfUrl": "http://hdl.handle.net/2060/20190002542", "es": "会议论文"}')
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
