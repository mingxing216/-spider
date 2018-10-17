# -*-coding:utf-8-*-

'''
知网期刊爬虫启动文件
'''
import sys
import os
import time
import threadpool
import pprint
import hashlib
import json
import hashlib
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from log import log
from utils import redis_dbutils
from Project.ZhiWangPeriodicalProject.services import zhiwang_periodical_serveice
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider
from Project.ZhiWangPeriodicalProject.dao import mysql_server

logname = 'zhiwang_periodical'
logging = log.ILog(logname)


class StartMain(object):
    def __init__(self):
        # 期刊时间列表种子
        self.qiKanTimeListUrl = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'

    def handle(self, urldata):
        return_data = {}
        text_url = urldata['url']
        # text_url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=JAXG201704006&tableName=CJFDLAST2017'
        urldata_qiKanUrl = urldata['qiKanUrl']
        # 服务对象
        server = zhiwang_periodical_serveice.zhiwangPeriodocalService()
        # 爬虫对象
        spider = zhiwang_periodical_spider.SpiderMain()
        # 获取文章页html源码
        article_html = spider.getRespForGet(url=text_url)
        if article_html:
            # ========================获取数据==========================
            # 获取期刊名称
            return_data['qiKanMingCheng'] = server.getQiKanMingCheng(article_html)
            # 获取关联文档
            return_data['guanLianWenDang'] = {}
            # 获取参考文献
            return_data['guanLianCanKaoWenXian'] = server.getGuanLianCanKaoWenXian(url=text_url)

            # 获取文章种子sha1加密
            return_data['sha'] = hashlib.sha1(text_url.encode('utf-8')).hexdigest()
            # 获取时间【年】
            return_data['shiJian'] = server.getshiJian(article_html)
            # 获取页数
            return_data['yeShu'] = server.getYeShu(article_html)
            # 获取关联图书期刊
            return_data['guanLianTuShuQiKan'] = server.getGuanLianTuShuQiKan(urldata_qiKanUrl)
            #获取作者
            return_data['zuoZhe'] = server.getZuoZhe(article_html)
            # 获取文章标题
            return_data['title'] = server.getArticleTitle(article_html)
            # 获取关联企业机构
            return_data['guanLianQiYeJiGou'] = server.getGuanLianQiYeJiGou(article_html)
            # 获取下载PDF下载链接
            return_data['xiaZai'] = server.getXiaZai(article_html)
            # 类别
            return_data['ss'] = '论文'
            # 获取关键词
            return_data['guanJianCi'] = server.getGuanJianCi(article_html)
            # 获取作者单位
            return_data['zuoZheDanWei'] = server.getZuoZheDanWei(article_html)
            # 生成key字段
            return_data['key'] = text_url
            # 获取大小
            return_data['daXiao'] = server.getDaXiao(article_html)
            # 获取在线阅读地址
            return_data['zaiXianYueDu'] = server.getZaiXianYueDu(article_html)
            # 获取分类号
            return_data['zhongTuFenLeiHao'] = server.getZhongTuFenLeiHao(article_html)
            # 获取下载次数
            return_data['xiaZaiCiShu'] = server.getXiaZaiCiShu(article_html)
            # 生成ws字段
            return_data['ws'] = '中国知网'
            # 生成url字段
            return_data['url'] = text_url
            # 生成biz字段
            return_data['biz'] = '文献大数据'
            # 获取关联人物
            return_data['guanLianRenWu'] = server.getGuanLianRenWu(article_html)
            # 生成ref字段
            return_data['ref'] = text_url
            # 获取期号
            return_data['qiHao'] = server.getQiHao(article_html)
            # 获取引证文献
            # return_data['guanLianYinZhengWenXian'] = server.getGuanLianYinZhengWenXian(url=text_url)
            # 获取所在页码
            return_data['suoZaiYeMa'] = server.getSuoZaiYeMa(article_html)
            # 获取摘要
            return_data['zhaiYao'] = server.getZhaiYao(article_html)
            # 生成es字段
            return_data['ex'] = '期刊论文'
            # 生成clazz字段
            return_data['clazz'] = '论文_期刊论文'
            # 获取基金
            return_data['jiJin'] = server.getJiJin(article_html)
            # 获取文内图片
            return_data['wenNeiTuPian'] = server.getWenNeiTuPian(article_html, text_url)
            # 获取doi
            return_data['shuZiDuiXiangBiaoShiFu'] = server.getDoi(article_html)
            # 生成来源分类字段
            return_data['laiYuanFenLei'] = ''
            # 生成学科类别分类
            return_data['xueKeLeiBie'] = urldata['xueKeLeiBie']

            # 生成关联人物url队列
            for man_url in return_data["guanLianRenWu"]:
                url = man_url['url']
                redis_dbutils.saveSet('qikanrenwu', url)

            # 生成关联企业机构url队列
            for jiGou in return_data["guanLianQiYeJiGou"]:
                url = jiGou['url']
                redis_dbutils.saveSet('qikanjigou', url)

            sha = return_data['sha']
            title = return_data['title']

            return_data = json.dumps(return_data)

            # 数据入库
            mysql_server.saveOrUpdate(sha, title, return_data)
            logging.info('{}: OK'.format(sha))

    def spiderRun(self, url_list):
        '''
        抓取文章数据
        :param url_list: 文章种子列表
        :return: 
        '''
        # 创建MAX_THREAD_SIZE个线程池
        pool = threadpool.ThreadPool(len(url_list))
        # 创建handle函数为线程, 传入音乐人信息列表
        requests = threadpool.makeRequests(self.handle, url_list)
        # 将所有要执行的线程扔进线程池并执行线程
        [pool.putRequest(req) for req in requests]
        # 等待所有线程执行完毕再继续下一步
        pool.wait()
        # for url in url_list:
        #     self.handle(url)
        #     break

    def task_processing(self, redis_key, index_url_data, server, spider):
        '''
        任务处理及抓取分配函数 
        :param redis_key: redis任务队列名
        :param index_url_data: 获取到的任务数据
        :param server: 服务对象
        :param spider: 爬虫对象
        :return: 
        '''
        url_data = index_url_data.decode('utf-8')
        url_data = eval(url_data)
        qiKanUrl = url_data['url']
        xueKeLeiBie = url_data['column_name']
        qiKanUrlSha1 = hashlib.sha1(qiKanUrl.encode('utf-8')).hexdigest()
        # 查询当前任务是否已抓取过
        if redis_dbutils.sismember('completed', qiKanUrlSha1):

            return
        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrl, pcode, pykm = server.qiKanTimeListUrl(qiKanUrl, self.qiKanTimeListUrl)
        # 获取期刊时间列表页html源码
        qikanTimeListHtml = spider.getRespForGet(qiKanTimeListUrl)
        # 获取期刊【年】、【期】
        qiKanTimeList = server.getQiKanTimeList(qikanTimeListHtml)
        # 循环获取指定年、期页文章列表页种子
        for qikan_year in qiKanTimeList:
            # 获取文章列表页种子
            articleListUrl = server.getArticleListUrl(qikan_year, pcode, pykm)
            for articleUrl in articleListUrl:
                # 获取文章列表页html源码
                article_list_html = spider.getRespForGet(articleUrl)
                # 获取文章种子列表
                article_url_list = server.getArticleUrlList(article_list_html, qiKanUrl, xueKeLeiBie)
                # 抓取数据
                self.spiderRun(article_url_list)

        # 将当前任务存入已抓取队列
        redis_dbutils.saveSet('completed', qiKanUrlSha1)
        # 队列中删除已完成任务
        redis_dbutils.srem(redis_key, url_data)

        logging.info('The current task is completed: {}'.format(qiKanUrlSha1))

    def run(self):
        # 服务对象
        server = zhiwang_periodical_serveice.zhiwangPeriodocalService()
        # 爬虫对象
        spider = zhiwang_periodical_spider.SpiderMain()
        while True:
            # 从redis获取任务
            redis_key = 'article_qikan_queue_1'
            index_url_data = redis_dbutils.queue_spop(key=redis_key, lockname='zhiwang_article_lock')
            # 如果当前队列有数据
            if index_url_data:
                # 任务处理
                self.task_processing(redis_key, index_url_data, server, spider)
            else:
                redis_key = 'article_qikan_queue_2'
                index_url_data = redis_dbutils.queue_spop(key=redis_key, lockname='zhiwang_article_lock')
                if index_url_data:
                    # 任务处理
                    self.task_processing(redis_key, index_url_data, server, spider)
                else:
                    logging.error('redis don\'t have task!!')
                    time.sleep(600)
                    continue

if __name__ == '__main__':

    main = StartMain()
    po = Pool(int(settings.ZHIWANG_PERIODOCAL_SPIDER_PROCESS))
    for i in range(int(settings.ZHIWANG_PERIODOCAL_SPIDER_PROCESS)):
        po.apply_async(func=main.run)
    po.close()
    po.join()