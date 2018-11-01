# -*-coding:utf-8-*-

'''
知网期刊爬虫启动文件
'''
import sys
import os
import time
import json
import hashlib
import threading
import multiprocessing
from multiprocessing import Lock
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from log import log
from utils import redispool_utils
from utils import mysqlpool_utils
# from utils import mysql_dbutils
from Project.ZhiWangPeriodicalProject.services import serveice
from Project.ZhiWangPeriodicalProject.spiders import zhiwang_periodical_spider
from Project.ZhiWangPeriodicalProject.dao import sql_dao

LOGNAME = 'zhiwang_periodical'
LOGGING = log.ILog(LOGNAME)

# 服务对象
server = serveice.zhiwangPeriodocalService()
# 爬虫对象
spider = zhiwang_periodical_spider.SpiderMain()


class StartMain(object):
    def __init__(self):
        # 期刊时间列表种子
        self.qiKanTimeListUrl = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 第一根栏目名
        self.first_name = 'article_qikan_queue_1'
        # 最后根栏目名
        self.last_name = 'article_qikan_queue_2'
        # Manager
        manager = multiprocessing.Manager()
        # 期刊任务队列
        self.qikan_q = manager.Queue(500)
        self.data = []

    def handle(self, redis_client, mysql_client, urldata):
        return_data = {}
        text_url = urldata['url']
        sha = hashlib.sha1(text_url.encode('utf-8')).hexdigest()
        # 查询当前文章是否被抓取过
        status = sql_dao.getStatus(mysql_client=mysql_client, sha=sha)
        if status:
            urldata_qiKanUrl = urldata['qiKanUrl']
            # 获取文章页html源码
            article_html = spider.getRespForGet(redis_client=redis_client, url=text_url)
            if article_html:
                # ========================获取数据==========================
                # 获取期刊名称
                return_data['qiKanMingCheng'] = server.getQiKanMingCheng(article_html)
                # 获取关联文档
                return_data['guanLianWenDang'] = {}
                # 获取参考文献
                return_data['guanLianCanKaoWenXian'] = server.getGuanLianCanKaoWenXian(redis_client=redis_client, spider=spider, url=text_url)
                # 获取文章种子sha1加密
                return_data['sha'] = sha
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
                return_data['faBuDanWei'] = server.getZuoZheDanWei(article_html)
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
                # 生成ref字段
                return_data['ref'] = text_url
                # 获取期号
                return_data['qiHao'] = server.getQiHao(article_html)
                # 获取引证文献
                # return_data['guanLianYinZhengWenXian'] = server.getGuanLianYinZhengWenXian(redis_client=redis_client, spider=spider, url=text_url)
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
                return_data['wenNeiTuPian'] = server.getWenNeiTuPian(redis_client=redis_client, spider=spider, html=article_html, url=text_url)
                # 获取doi
                return_data['shuZiDuiXiangBiaoShiFu'] = server.getDoi(article_html)
                # 生成来源分类字段
                return_data['laiYuanFenLei'] = ''
                # 生成学科类别分类
                return_data['xueKeLeiBie'] = urldata['xueKeLeiBie']
                # 获取关联人物
                guanLianRenWu_Data = server.getGuanLianRenWu(redis_client=redis_client, spider=spider, html=article_html, year=return_data['shiJian'])
                return_data['guanLianRenWu'] = []
                for man in guanLianRenWu_Data:
                    data = {}
                    data['sha'] = man['sha']
                    data['ss'] = '人物'
                    data['url'] = man['url']
                    data['name'] = man['name']
                    return_data['guanLianRenWu'].append(data)

                # 生成关联人物url队列
                for man_url in return_data["guanLianRenWu"]:
                    url = man_url['url']
                    redispool_utils.sadd(redis_client=redis_client, key='qikanrenwu', value=url)

                # 生成关联企业机构url队列
                for jiGou in return_data["guanLianQiYeJiGou"]:
                    url = jiGou['url']
                    redispool_utils.sadd(redis_client=redis_client, key='qikanjigou', value=url)

                # 生成关联人物表数据入库
                for renWuData in guanLianRenWu_Data:
                    insert_renwu_data = {}
                    try:
                        insert_renwu_data['ref'] = renWuData['url']
                    except:
                        insert_renwu_data['ref'] = ''
                    try:
                        insert_renwu_data['title'] = renWuData['name']
                    except:
                        insert_renwu_data['title'] = ''
                    try:
                        insert_renwu_data['guanLianQiYeJiGou'] = [{"sha": renWuData['suoZaiDanWei']['单位sha1'],
                                                                   "ss": "机构",
                                                                   "url": renWuData['suoZaiDanWei']['单位url'],}]
                    except:
                        insert_renwu_data['guanLianQiYeJiGou'] = []
                    try:
                        insert_renwu_data['sha'] = renWuData['sha']
                    except:
                        insert_renwu_data['sha'] = ''
                    try:
                        insert_renwu_data['suoZaiDanWei'] = [{"所在单位": renWuData["suoZaiDanWei"]['所在单位'],
                                                              "时间": renWuData['suoZaiDanWei']['时间']}]
                    except:
                        insert_renwu_data['suoZaiDanWei'] = []
                    insert_renwu_data['ss'] = '人物'
                    insert_renwu_data['ws'] = '中国知网'
                    insert_renwu_data['clazz'] = '人物'
                    insert_renwu_data['es'] = '期刊论文'
                    try:
                        insert_renwu_data['key'] = renWuData['url']
                    except:
                        insert_renwu_data['key'] = ''
                    try:
                        insert_renwu_data['url'] = renWuData['url']
                    except:
                        insert_renwu_data['url'] = ''
                    insert_renwu_data['biz'] = '文献大数据'
                    renwu_sha = insert_renwu_data['sha']
                    renwu_title = insert_renwu_data['title']

                    input_data = json.dumps(insert_renwu_data)


                    # 存入关联人物数据库
                    sql_dao.saveRenWu(mysql_client=mysql_client, sha=renwu_sha, title=renwu_title, data=input_data)
                    # break


                title = return_data['title']

                return_data = json.dumps(return_data)

                # 数据入库
                sql_dao.saveOrUpdate(mysql_client=mysql_client, sha=sha, title=title, data=return_data)
                LOGGING.info('数据已保存: {}'.format(sha))

        else:
            LOGGING.info('{}: 已被抓取过'.format(sha))

    def spiderRun(self):
        '''
        抓取文章数据
        :param url_list: 文章种子列表
        :return:
        '''
        # redis对象
        redis_client = redispool_utils.createRedisPool()
        # mysql连接池
        mysql_client = mysqlpool_utils.createMysqlPool()
        while True:
            article_url_list = []
            for i in range(100):
                if self.qikan_q.qsize() != 0:
                    try:
                        a = self.qikan_q.get_nowait()
                    except:
                        break
                    else:
                        article_url_list.append(a)
            if not article_url_list:
                LOGGING.error('文章队列无数据')
                time.sleep(10)
                continue

            else:
                thread_pool = ThreadPool()
                for article_url in article_url_list:
                    thread_pool.apply_async(func=self.handle, args=(redis_client, mysql_client, article_url))
                thread_pool.close()
                thread_pool.join()

    def task_processing(self, redis_client, redis_key, index_url_data):
        '''
        任务处理及抓取分配函数
        :param redis_key: redis任务队列名
        :param index_url_data: 获取到的任务数据
        :return:
        '''
        url_data = eval(index_url_data)
        qiKanUrl = url_data['url']
        xueKeLeiBie = url_data['column_name']

        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrl, pcode, pykm = server.qiKanTimeListUrl(qiKanUrl, self.qiKanTimeListUrl)
        # 获取期刊时间列表页html源码
        qikanTimeListHtml = spider.getRespForGet(redis_client=redis_client, url=qiKanTimeListUrl)
        # 获取期刊【年】、【期】
        qiKanTimeList = server.getQiKanTimeList(qikanTimeListHtml)

        # 循环获取指定年、期页文章列表页种子
        for qikan_year in qiKanTimeList:
            # 获取文章列表页种子
            articleListUrl = server.getArticleListUrl(qikan_year, pcode, pykm)
            for articleUrl in articleListUrl:
                # 获取文章列表页html源码
                article_list_html = spider.getRespForGet(redis_client=redis_client, url=articleUrl)
                # 获取文章种子列表
                article_url_list = server.getArticleUrlList(article_list_html, qiKanUrl, xueKeLeiBie)
                if article_url_list:
                    for article_url in article_url_list:
                        self.qikan_q.put(article_url)

                    LOGGING.info('期刊任务队列数量: {}'.format(self.qikan_q.qsize()))

    def run(self):
        # redis对象
        redis_client = redispool_utils.createRedisPool()
        while True:
            # 从redis获取任务
            redis_key = self.first_name
            index_url_data = redispool_utils.queue_spop(redis_client=redis_client, key=redis_key, lockname='zhiwang_article_lock')

            # 如果当前队列有数据
            if index_url_data:
                # 任务处理
                self.task_processing(redis_client=redis_client, redis_key=redis_key, index_url_data=index_url_data)

            else:
                redis_key = self.last_name
                index_url_data = redispool_utils.queue_spop(redis_client=redis_client, key=redis_key, lockname='zhiwang_article_lock')

                if index_url_data:
                    # 任务处理
                    self.task_processing(redis_client=redis_client, redis_key=redis_key, index_url_data=index_url_data)

                else:
                    LOGGING.error('redis队列空！！！600秒后重新尝试获取')
                    time.sleep(600)
                    continue


if __name__ == '__main__':

    main = StartMain()
    po = Pool(int(settings.ZHIWANG_PERIODOCAL_SPIDER_PROCESS) * 2)
    for i in range(int(settings.ZHIWANG_PERIODOCAL_SPIDER_PROCESS) * 2):
        po.apply_async(func=main.run)
        po.apply_async(func=main.spiderRun)
    po.close()
    po.join()