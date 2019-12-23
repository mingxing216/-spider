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
from Project.ZhiWang.middleware import download_middleware
from Project.ZhiWang.service import service
from Project.ZhiWang.dao import dao
from Project.ZhiWang import config

log_file_dir = 'ZhiWang'  # LOG日志存放路径
LOGNAME = '<知网_发明公开_data>'  # LOG名
NAME = '知网_发明公开_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.GongKaiDownloader(logging=LOGGING,
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

    def __getResp(self, func, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(10):
            resp = func(url=url, mode=mode, s=s, data=data, cookies=cookies, referer=referer)
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
            return None

    # 获取公告实体字段
    def announcement(self, gonggao_url, zhuanli_url, zhuanli_sha):
        # 公告数据存储字典
        announce_data = {}
        url = gonggao_url

        # 访问公告页面，获取响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('公告页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PATENT, sha=zhuanli_sha)
            return

        response = resp.text

        # 获取公告标题
        titles = self.server.getTitles(response)
        # 获取所有公告标签，并遍历
        nodes = self.server.getGongGaoNodes(response)

        if nodes:
            for node in nodes:
                # 申请号
                announce_data['shenQingHao'] = self.server.getShenQingHao(response)
                for i in range(len(titles)):
                    if titles[i] == '法律状态公告日':
                        # 法律状态公告日
                        faLvZhuangTaiGongGaoRi = self.server.getGongGaoInfo(node, i)
                        if faLvZhuangTaiGongGaoRi:
                            try:
                                announce_data['faLvZhuangTaiGongGaoRi'] = str(datetime.strptime(faLvZhuangTaiGongGaoRi, '%Y-%m-%d'))
                            except:
                                announce_data['faLvZhuangTaiGongGaoRi'] = faLvZhuangTaiGongGaoRi
                        else:
                            announce_data['faLvZhuangTaiGongGaoRi'] = ""

                    if titles[i] == '法律状态':
                        # 法律状态
                        announce_data['faLvZhuangTai'] = self.server.getGongGaoInfo(node, i)

                    if titles[i] == '法律状态信息':
                        # 法律状态信息
                        announce_data['faLvZhuangTaiXinXi'] = self.server.getGongGaoInfo(node, i)

                # 关联专利
                announce_data['guanLianZhuanLi'] = self.server.guanLianZhuanLi(url=zhuanli_url, sha=zhuanli_sha)
                # 获取主键
                sha = url + announce_data['faLvZhuangTaiGongGaoRi'] + announce_data['faLvZhuangTai'] + announce_data['faLvZhuangTaiXinXi']
                sha1 = hashlib.sha1(sha.encode('utf-8')).hexdigest()
                # ===================公共字段
                # url
                announce_data['url'] = url
                # 生成key
                announce_data['key'] = url
                # 生成sha
                announce_data['sha'] = sha1
                # 生成ss ——实体
                announce_data['ss'] = '公告'
                # 生成es ——栏目名称
                announce_data['es'] = '发明公开'
                # 生成ws ——目标网站
                announce_data['ws'] = '中国知网'
                # 生成clazz ——层级关系
                announce_data['clazz'] = '公告_专利'
                # 生成biz ——项目
                announce_data['biz'] = '文献大数据'
                # 生成ref
                announce_data['ref'] = ''

                # 保存数据到Hbase
                sto = self.dao.saveDataToHbase(data=announce_data)

                if not sto:
                    LOGGING.error('公告数据存储失败, url: {}'.format(url))
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_PATENT, sha=zhuanli_sha)
                else:
                    LOGGING.info('公告数据存储成功, sha: {}'.format(sha1))

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        old_url = task_data['url']
        url = old_url.replace('http', 'https')
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET')
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PATENT, sha=sha)
            return

        response = resp.text
        # with open ('profile.html', 'w') as f:
        #     f.write(response)
        # return

        # 获取标题
        save_data['title'] = self.server.getTitle(response)
        # 获取申请号
        save_data['shenQingHao'] = self.server.getField(response, '申请号')
        # 获取申请日
        shenQingRi = self.server.getField(response, '申请日')
        if shenQingRi:
            try:
                save_data['shenQingRi'] = str(datetime.strptime(shenQingRi, '%Y-%m-%d'))
            except:
                save_data['shenQingRi'] = shenQingRi
        else:
            save_data['shenQingRi'] = ""
        # 获取公开号
        save_data['gongKaiHao'] = self.server.getField(response, '公开号')
        # 获取公开日
        gongKaiRi = self.server.getField(response, '公开日')
        if gongKaiRi:
            try:
                save_data['gongKaiRi'] = str(datetime.strptime(gongKaiRi, '%Y-%m-%d'))
            except:
                save_data['gongKaiRi'] = gongKaiRi
        else:
            save_data['gongKaiRi'] = ""
        # 获取申请人
        save_data['shenQingRen'] = self.server.getField(response, '申请人')
        # 获取申请人地址
        save_data['shenQingRenDiZhi'] = self.server.getField(response, '地址')
        # 获取发明人
        save_data['faMingRen'] = self.server.getField(response, '发明人')
        # 获取国际申请
        save_data['guoJiShenQing'] = self.server.getField(response, '国际申请')
        # 获取国际公布
        save_data['guoJiGongBu'] = self.server.getField(response, '国际公布')
        # 获取代理机构
        save_data['daiLiJiGou'] = self.server.getField(response, '专利代理机构')
        # 获取代理人
        save_data['daiLiRen'] = self.server.getField(response, '代理人')
        # 获取国省代码
        save_data['guoShengDaiMa'] = self.server.getField(response, '国省代码')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getHtml(response, '摘要')
        # 获取主权项
        save_data['zhuQuanXiang'] = self.server.getHtml(response, '主权项')
        # 获取页数
        save_data['yeShu'] = self.server.getField(response, '页数')
        # 获取IPC主分类号
        save_data['IPCzhuFenLeiHao'] = self.server.getField(response, '主分类号')
        # 获取IPC分类号
        save_data['IPCfenLeiHao'] = self.server.getField(response, '专利分类号')
        # 获取下载
        save_data['xiaZai'] = self.server.getXiaZai(response)
        # 获取专利类型
        save_data['zhuanLiLeiXing'] = "发明公开"
        # 获取专利国别
        save_data['zhuanLiGuoBie'] = self.server.getZhuanLiGuoBie(save_data['gongKaiHao'])

        # 获取公告url
        gongGao = self.server.getGongGao(response)
        if gongGao:
            self.announcement(gonggao_url=gongGao, zhuanli_url=url, zhuanli_sha=sha)

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '专利'
        # 生成es ——栏目名称
        save_data['es'] = '发明公开'
        # 生成ws ——目标网站
        save_data['ws'] = '中国知网'
        # 生成clazz ——层级关系
        save_data['clazz'] = '专利'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 返回sha为删除任务做准备
        old_sha = hashlib.sha1(old_url.encode('utf-8')).hexdigest()
        return old_sha

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
            self.dao.deleteTask(table=config.MYSQL_PATENT, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PATENT, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_FM_PATENT, count=20, lockname=config.REDIS_FM_PATENT_LOCK)
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
        # main.run(task='{"url":"http://dbpub.cnki.net/grid2008/dbpub/detail.aspx?dbcode=SCPD&dbname=SCPD2017&filename=CN106170564A"}')
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
