# -*-coding:utf-8-*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import json
import hashlib
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Utils import timers
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME, STO_HOST, STO_PORT, STO_USER, STO_PASS, STO_NAME

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊论文_task'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_LunWen(logging=logger)
        self.spi_dao = dao.Dao(logging=logger,
                               host=SPI_HOST, port=SPI_PORT, user=SPI_USER, pwd=SPI_PASS, db=SPI_NAME,
                               mysqlpool_number=config.MYSQL_POOL_NUMBER,
                               redispool_number=config.REDIS_POOL_NUMBER)
        self.sto_dao = dao.Dao(logging=logger,
                               host=STO_HOST, port=STO_PORT, user=STO_USER, pwd=STO_PASS, db=STO_NAME,
                               mysqlpool_number=config.MYSQL_POOL_NUMBER,
                               redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化期刊时间列表种子模板
        self.timer = timers.Timer()
        self.index_url = 'https://navi.cnki.net/KNavi/Journal.html'
        self.qikan_time_url = 'https://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunwen_url = 'https://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'
        # 记录存储种子数量
        self.num = 0

    def _get_resp(self, url, method, s=None, data=None, host=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download.get_resp(s=s, url=url, method=method, data=data, host=host,
                                          cookies=cookies, referer=referer)
            if resp:
                if resp['status'] == 200:
                    if '请输入验证码' in resp['data'].text or len(resp['data'].text) < 10:
                        logger.error('captcha | 出现验证码: {}'.format(url))
                        continue
            return resp
        else:
            return

    def remove_duplicate(self, old_list, new_list):
        new_issue_list = []
        old_issue_list = []
        for old in old_list:
            old_tuple = []
            for v in old.values():
                old_tuple.append(v)
            old_issue_list.append(tuple(old_tuple))

        for new_issue in new_list:
            if new_issue not in old_issue_list:
                new_issue_list.append(new_issue)
                
        return new_issue_list

    def run(self):
        self.timer.start()
        while True:
            # 获取任务
            category = self.spi_dao.get_one_task_from_redis(key=config.REDIS_QIKAN_CATALOG)
            # category = '{"url": "https://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JYJX", "sha": "725f5c55d58f0b8871078b00de7c4284d9c66e19", "s_xueKeLeiBie": "医药卫生科技_医药卫生综合", "s_zhongWenHeXinQiKanMuLu": ""}'
            # print(category)
            if category:
                try:
                    # # 获取cookie
                    # self._get_resp(url=self.index_url, method='GET')
                    # 数据类型转换
                    task = json.loads(category)
                    # print(task)
                    # 保存线程中的任务种子到临时队列
                    self.spi_dao.queue_one_task_to_redis(key=config.REDIS_CATALOG_TEMP, data=task)

                    qikan_url = task.get('url')
                    qikan_sha = task.get('sha')
                    xueke_leibie = task.get('s_xueKeLeiBie')

                    # # 创建cookies
                    # self._get_resp(url=qikan_url, method='GET', s=self.s)
                    # # 设置会话cookies
                    # print(self.s.cookies)

                    # 生成单个知网期刊的时间列表种子
                    qikan_time_list_url, pcode, pykm = self.server.qikan_time_list_url(qikan_url, self.qikan_time_url)
                    # print(qikan_time_list_url, pcode, pykm)
                    # 获取期刊时间列表页html源码
                    if qikan_time_list_url:
                        # 获取期刊【年】、【期】列表
                        # 循环获取指定年、期页文章列表页种子
                        # 判断附加信息中是否有年期列表
                        if task.get('issues_list'):
                            issues_list = task.get('issues_list')
                        else:
                            qikanTimeListHtml = self._get_resp(url=qikan_time_list_url, method='GET',
                                                               host='navi.cnki.net')
                            if qikanTimeListHtml is None:
                                logger.error('catalog | 期刊时间列表页获取失败, url: {}'.format(qikan_time_list_url))
                                # 删除临时队列中该种子
                                self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                # 队列一条任务
                                self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                continue

                            if not qikanTimeListHtml['data']:
                                logger.error('catalog | 期刊时间列表页获取失败, url: {}'.format(qikan_time_list_url))
                                # 删除临时队列中该种子
                                self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                # 队列一条任务
                                self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                continue

                            issues_list = self.server.get_qikan_time_list(qikanTimeListHtml['data'])
                            if issues_list:
                                # 参数
                                journal_info = ['中国知网', pykm, qikan_url, '张明星']
                                # 从mysql获取该期刊年卷期信息
                                year_issue_list = self.sto_dao.get_journal_info_from_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                                                           ws='中国知网', journal_id=pykm)
                                if not year_issue_list:
                                    self.sto_dao.record_journal_info_to_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                                              data=issues_list,
                                                                              para=journal_info)
                                else:
                                    issues_list = self.remove_duplicate(year_issue_list, issues_list)
                                    if issues_list:
                                        self.sto_dao.record_journal_info_to_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                                                  data=issues_list,
                                                                                  para=journal_info)


                        if issues_list is None:
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                            continue

                        if issues_list:
                            for year_issue in issues_list:
                                # 获取文章列表页种子
                                article_url = self.server.get_article_list_url(url=self.lunwen_url,
                                                                               data=year_issue,
                                                                               pcode=pcode,
                                                                               pykm=pykm)
                                # print(article_url)
                                # 获取论文列表页html源码
                                if article_url:
                                    article_list_html = self._get_resp(url=article_url, method='GET', host='navi.cnki.net')
                                    if article_list_html is None:
                                        logger.error('catalog | 论文列表页html源码获取失败, url: {}'.format(article_url))
                                        # 删除临时队列中该种子
                                        self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                        # 队列一条任务
                                        issue_index = issues_list.index(year_issue)
                                        task['issues_list'] = issues_list[issue_index:]
                                        self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                        break

                                    if not article_list_html['data']:
                                        logger.error('catalog | 论文列表页html源码获取失败, url: {}'.format(article_url))
                                        # 删除临时队列中该种子
                                        self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                        # 队列一条任务
                                        issue_index = issues_list.index(year_issue)
                                        task['issues_list'] = issues_list[issue_index:]
                                        self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                        break

                                    if '暂无目录信息' in article_list_html['data'].text:
                                        logger.error('catalog | 列表页无内容, url: {}'.format(article_url))
                                        continue

                                    # 获取论文详情种子
                                    article_url_list = self.server.get_article_url_list(article_list_html['data'],
                                                                                        qikan_url, xueke_leibie, year_issue)
                                    if article_url_list:
                                        for paper_url in article_url_list:
                                            # print(paper_url)
                                            # 存储种子
                                            self.num += 1
                                            logger.info('profile | 已抓种子数量: {}'.format(self.num))
                                            paper_sha = hashlib.sha1(paper_url.get('url').encode('utf-8')).hexdigest()
                                            mysql_paper = 'job_paper_{}'.format(paper_sha[0])
                                            self.sto_dao.save_task_to_mysql(table=mysql_paper, memo=paper_url, ws='中国知网',
                                                                            es='期刊论文')

                                        # 更新mysql期刊信息表中年期状态
                                        self.sto_dao.update_journal_info_to_mysql(table=config.MYSQL_JOURNAL_INFO,
                                                                                  ws='中国知网',
                                                                                  journal_id=pykm,
                                                                                  year=year_issue[0],
                                                                                  issue=year_issue[1])

                                    else:
                                        logger.error('profile | 详情种子获取失败, url: {}'.format(article_url))
                                        # 删除临时队列中该种子
                                        self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                        # 队列一条任务
                                        issue_index = issues_list.index(year_issue)
                                        task['issues_list'] = issues_list[issue_index:]
                                        self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                        break
                                else:
                                    logger.error('catalog | 论文{}年{}期列表页获取失败'.format(year_issue[0], year_issue[1]))
                                    # 删除临时队列中该种子
                                    self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                    # 队列一条任务
                                    issue_index = issues_list.index(year_issue)
                                    task['issues_list'] = issues_list[issue_index:]
                                    self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                                    break
                            else:
                                logger.info('catalog | 年、期列表获取完毕, url: {}'.format(qikan_url))
                                # 删除临时队列中该种子
                                self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                                # 已完成任务
                                self.spi_dao.finish_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=qikan_sha)
                        else:
                            logger.error('catalog | 年、期列表获取失败, url: {}'.format(qikan_url))
                            # 删除临时队列中该种子
                            self.spi_dao.remove_one_task_from_redis(key=config.REDIS_CATALOG_TEMP, data=task)
                            # 队列一条任务
                            self.spi_dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                            continue

                except Exception as e:
                    logger.error('except | 执行错误: {}'.format(e))
                    continue

            else:
                logger.info('task | 队列中已无任务，结束程序 | use time: {}'.format(self.timer.use_time()))
                return

    def queue_catalog(self):
        while True:
            # 查询redis队列中任务数量
            url_number = self.spi_dao.select_task_number(key=config.REDIS_QIKAN_CATALOG)
            if url_number <= config.MAX_QUEUE_REDIS / 10:
                logger.info('queue | redis中任务已少于 {}, 开始新增队列任务'.format(int(config.MAX_QUEUE_REDIS / 10)))
                # 获取任务
                new_task_list = self.spi_dao.get_task_list_from_mysql(table=config.MYSQL_MAGAZINE, ws='中国知网', es='期刊',
                                                                      count=15000)
                # print(new_task_list)
                # 队列任务
                self.spi_dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_QIKAN_CATALOG, data=new_task_list)
            else:
                logger.info('queue | redis剩余{}个任务'.format(url_number))

            time.sleep(1)


def queue_task():
    try:
        main = SpiderMain()
        main.queue_catalog()
    except:
        logger.exception(str(traceback.format_exc()))


def start():
    try:
        main = SpiderMain()
        main.run()
    except:
        logger.exception(str(traceback.format_exc()))


def process_start():
    # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

    # # 创建gevent协程
    # g_list = []
    # for i in range(8):
    #     s = gevent.spawn(self.run)
    #     g_list.append(s)
    # gevent.joinall(g_list)

    # self.run()

    # 创建线程池
    tpool = ThreadPoolExecutor(max_workers=1)
    for i in range(1):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    # process_start()
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=1)
    # ppool.submit(queue_task)
    for i in range(1):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
