# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
import re
import json
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
# from Utils import mysql_dbutils
from ObjectBeas.ZhiWangPeriodicalProject.services import serveice
from ObjectBeas.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider
from ObjectBeas.ZhiWangPeriodicalProject.dao import sql_dao

log_file_dir = 'zhiwang_qikan_spider_main'
LOGNAME = '<期刊_期刊爬虫>'
LOGGING = log.ILog(log_file_dir, LOGNAME)

# 服务对象
server = serveice.ZhiWangQiKanService()
# 爬虫对象
spider = zhiwang_periodical_spider.SpiderMain()


class SpiderMain(object):
    def __init__(self):
        # 第一个期刊集合名
        self.first_name = 'qikan_queue_1'
        # 最后一个期刊集合名
        self.last_name = 'qikan_queue_2'
        # 第一个期刊集合数据
        self.first_data = []
        # 最后一个期刊集合数据
        self.last_data = []
        # 期刊总集合
        self.data = []
        manager = multiprocessing.Manager()
        # 期刊队列
        self.url_q = manager.Queue()


    def handel(self,redis_client, mysql_client, url_data):
        # url_data = {'column_name': '社会科学II_初等教育', 'title': '第二课堂(C)', 'url': 'http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=DEKT'}
        return_data = {}
        url = url_data['url']
        column_name = url_data['column_name']

        if '|' in column_name:
            xueKeLeiBie = re.findall(r'(.*)\|', column_name)[0]
            heXinQiKanDaoHang = column_name
        else:
            xueKeLeiBie = column_name
            heXinQiKanDaoHang = ''

        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 查询当前期刊是否被抓取过
        status = sql_dao.selectQiKanStatus(mysql_client=mysql_client, sha=sha)
        if status:
            # 获取期刊页html源码
            html = spider.getRespForGet(redis_client=redis_client, url=url, logging=LOGGING)
            # 生成ss字段
            return_data['ss'] = '期刊'
            # 生成ws字段
            return_data['ws'] = '中国知网'
            # 生成url字段
            return_data['url'] = url
            # 生成sha字段
            return_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            # 生成key字段
            return_data['key'] = url
            # 生成biz字段
            return_data['biz'] = '文献大数据'
            # 生成ref字段
            return_data['ref'] = url
            # 生成clazz字段
            return_data['clazz'] = '期刊_学术期刊'
            # 生成es字段
            return_data['es'] = '期刊'
            # 获取标题
            return_data['title'] = server.getTitle(html)
            #获取核心收录
            return_data['heXinShouLu'] = server.getHeXinShouLu(html)
            # 获取外文名称
            return_data['yingWenMingCheng'] = server.getYingWenMingCheng(html)
            # 获取图片
            return_data['biaoShi'] = server.getBiaoShi(html)
            # 获取曾用名
            return_data['cengYongMing'] = server.getData(html, '曾用刊名：')
            # 获取主办单位
            return_data['zhuBanDanWei'] = server.getData(html, '主办单位：')
            # 获取出版周期
            return_data['chuBanZhouQi'] = server.getData(html, '出版周期：')
            # 获取issn
            return_data['issn'] = server.getData(html, 'ISSN：')
            # 获取CH
            return_data['guoNeiKanHao'] = server.getData(html, 'CN：')
            # 获取出版地
            return_data['chuBanDi'] = server.getData(html, '出版地：')
            # 获取语种
            # TODO 语种有多值
            return_data['yuZhong'] = server.getData(html, '语种：')
            # 获取开本
            return_data['kaiBen'] = server.getData(html, '开本：')
            # 获取邮发代号
            return_data['youFaDaiHao'] = server.getData(html, '邮发代号：')
            # 获取创刊时间
            return_data['shiJian'] = {'Y': server.getData(html, '创刊时间：')}
            # 获取专辑名称
            return_data['zhuanJiMingCheng'] = server.getData2(html, '专辑名称：')
            # 获取专题名称
            return_data['zhuanTiMingCheng'] = server.getData2(html, '专题名称：')
            # 获取出版文献量
            try:
                return_data['chuBanWenXianLiang'] = {'u': '篇', 'v': re.findall(r'\d+', server.getData2(html, '出版文献量：'))[0]}
            except:
                return_data['chuBanWenXianLiang'] = {'u': '篇', 'v': 0}
            # 获取复合影响因子
            return_data['fuHeYingXiangYinZi'] = server.getFuHeYingXiangYinZi(html)
            # 获取综合影响因子
            return_data['zongHeYingXiangYinZi'] = server.getZongHeYingXiangYinZi(html)
            # 获取来源数据库
            return_data['laiYuanShuJuKu'] = server.getLaiYuanShuJuKu(html)
            # 获取期刊荣誉
            return_data['qiKanRongYu'] = server.getQiKanRongYu(html)
            # 获取来源分类
            return_data['laiYuanFenLei'] = ''
            # 获取关联主管单位
            return_data['guanLianZhuGuanDanWei'] = {}
            # 获取关联主办单位
            return_data['guanLianZhuBanDanWei'] = {}
            # 生成学科类别
            return_data['xueKeLeiBie'] = xueKeLeiBie
            # 生成核心期刊导航
            return_data['heXinQiKanDaoHang'] = heXinQiKanDaoHang

            sha = return_data['sha']
            title = return_data['title']
            return_data = json.dumps(return_data)
            # 数据入库
            sql_dao.saveQiKan(mysql_client=mysql_client, sha=sha, title=title, data=return_data, logging=LOGGING)

    def spider_run(self, redis_client, mysql_client, url_datas):
        po = ThreadPool(10)
        for url_data in url_datas:
            po.apply_async(func=self.handel, args=(redis_client, mysql_client, url_data,))

        po.close()
        po.join()

    def itegrationOfData(self):
        '''整合redis队列数据'''
        # redis对象
        redis_client = redispool_utils.createRedisPool()
        # 获取第一个栏目集合数据
        datas_1 = redis_client.smembers(self.first_name)
        for data1 in datas_1:
            data1 = data1.decode('utf-8')
            self.first_data.append(data1)
        # 获取最后一个栏目集合数据
        datas_2 = redis_client.smembers(self.last_name)
        for data2 in datas_2:
            data2 = data2.decode('utf-8')
            self.last_data.append(data2)

        for first_data in self.first_data:
            # 获取总集合内元素数量
            data_number = len(self.data)
            first_data = eval(first_data)
            first_column_name = first_data['column_name']
            first_url = first_data['url']
            for last_data in self.last_data:
                last_data = eval(last_data)
                last_column_name = last_data['column_name']
                last_url = last_data['url']
                if first_url == last_url:
                    name = first_column_name + '|' + last_column_name
                    first_data['column_name'] = name
                    self.data.append(first_data)

            # 获取总集合内元素数量
            data_number_two = len(self.data)
            if data_number == data_number_two:
                self.data.append(first_data)
                continue
            else:

                continue

        # 生成任务队列
        for data in self.data:
            self.url_q.put(data)
        LOGGING.info('队列已生成， 任务数量: {}'.format(self.url_q.qsize()))

    def run(self):
        # redis对象
        redis_client = redispool_utils.createRedisPool()
        # mysql对象
        mysql_client = mysqlpool_utils.createMysqlPool()
        while True:
            # 获取机构任务(100个)
            url_datas = []
            for i in range(100):
                if self.url_q.qsize() == 0:
                    break
                else:
                    try:
                        url_data = self.url_q.get_nowait()
                    except:
                        url_data = None
                    if url_data:
                        url_datas.append(url_data)
            if url_datas:
                LOGGING.info(self.url_q.qsize())
                self.spider_run(redis_client=redis_client, mysql_client=mysql_client, url_datas=url_datas)
            else:
                LOGGING.error('期刊队列任务结束')
                break

if __name__ == '__main__':
    spidermain = SpiderMain()
    spidermain.itegrationOfData()
    spidermain.run()
