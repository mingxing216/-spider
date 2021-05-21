# -*-coding:utf-8-*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import re
import time
import json
import random
import traceback
import hashlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Project.ZhiWangLunWen import config
from Utils import timers, hbase_pool
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊论文_check'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class CheckerMain(object):
    def __init__(self):
        super().__init__()
        self.timer = timers.Timer()
        # hbase存储对象
        self.hbase_obj = hbase_pool.HBasePool(host='mm-node5', logging=logger)

    def handle(self, task_data, data_dict):
        # print(task_data)
        url = task_data['url']
        # print(id)
        key = '中国知网|'
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()

        # ======================== 期刊论文实体数据 ===========================
        # 创建数据存储字典
        data_dict['quality_score'] = '100'
        data_dict['quality_score'] = '80'
        data_dict['quality_score'] = '0'

        # ====================================公共字段
        # url
        data_dict['url'] = url
        # 生成key
        data_dict['key'] = key
        # 生成sha
        data_dict['sha'] = sha
        # 生成ss ——实体
        data_dict['ss'] = '论文'
        # es ——栏目名称
        data_dict['es'] = '期刊论文'
        # 生成ws ——目标网站
        data_dict['ws'] = '中国知网'
        # 生成clazz ——层级关系
        data_dict['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        data_dict['biz'] = '文献大数据_论文'
        # 生成ref
        data_dict['ref'] = ''
        # 采集责任人
        data_dict['creator'] = '张明星'
        # 更新责任人
        data_dict['modified_by'] = ''
        # 采集服务器集群
        data_dict['cluster'] = 'crawler'
        # 元数据版本号
        data_dict['metadata_version'] = 'V1.2'
        # 采集脚本版本号
        data_dict['script_version'] = 'V1.4'

    def run(self):
        logger.debug('thread start')
        task_timer = timers.Timer()
        # 第一次请求的等待时间
        self.timer.start()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.debug('thread | wait download delay time | use time: {}'.format(self.timer.use_time()))
        # 单线程无限循环
        while True:
            # 获取任务
            logger.info('task start')
            task_timer.start()
            # task_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER, count=1,
            #                              lockname=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER_LOCK)
            task = self.dao.get_one_task_from_redis(key=config.REDIS_QIKAN_PAPER)
            # task = '{"theme": "", "url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=DATE200701035&dbname=CJFD2007", "xiaZai": "https://navi.cnki.net/knavi/Common/RedirectPage?sfield=XZ&q=nFrh4jEAHve1tEpBnJjmBUbXZotShkQUYyJLQuzx%mmd2BeY9nV0WaHVfnNQG4TiA8tcE&tableName=CJFD2007", "zaiXianYueDu": "https://navi.cnki.net/knavi/Common/RedirectPage?sfield=RD&dbCode=CJFD&filename=DATE200701035&tablename=CJFD2007&filetype=", "xueKeLeiBie": "信息科技_电信技术", "parentUrl": "https://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=DATE", "year": "2007", "issue": "01", "sha": "fd1afcf50a33a6f591000362f45bff090888b5cb"}'
            if task:
                # 创建数据存储列表
                data_dict = dict()
                # json数据类型转换
                task_data = json.loads(task)
                sha = task_data.get('sha')
                try:
                    # 获取字段值存入字典并返回sha
                    self.handle(task_data=task_data, data_dict=data_dict)
                    # 保存数据到Hbase
                    if not data_dict:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | No data.'.format(task_timer.use_time()))
                        continue
                    if 'sha' not in data_dict:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | Data Incomplete.'.format(task_timer.use_time()))
                        continue
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=data_dict)

                    if success:
                        # 已完成任务
                        self.dao.finish_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        # # 删除任务
                        # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                    else:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)

                    logger.info('task end | task success | use time: {}'.format(task_timer.use_time()))

                except:
                    logger.exception(str(traceback.format_exc()))
                    # 逻辑删除任务
                    self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                    logger.error('task end | task failed | use time: {}'.format(task_timer.use_time()))
            else:
                logger.info('task | 队列中已无任务')


def start():
    try:
        main = CheckerMain()
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
    tpool = ThreadPoolExecutor(max_workers=config.THREAD_NUM)
    for i in range(config.THREAD_NUM):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    # process_start()
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
