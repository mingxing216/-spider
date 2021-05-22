# -*-coding:utf-8-*-

"""

"""
import json
import os
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import traceback

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config
from Log import logging
from Utils import timers, hbase_pool, redis_pool
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊论文_check'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseChecher(object):
    def __init__(self):
        self.server = service.LunWen_Data(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           host=SPI_HOST, port=SPI_PORT, user=SPI_USER, pwd=SPI_PASS, db=SPI_NAME,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class CheckerMain(BaseChecher):
    def __init__(self, hostname):
        super().__init__()
        self.timer = timers.Timer()
        # redis对象
        self.redis_obj = redis_pool.RedisPoolUtils(10)
        # hbase对象
        self.hbase_obj = hbase_pool.HBasePool(host=hostname, logging=logger)

    def handle(self, task_list, data_list):
        self.timer.start()
        for task in task_list:
            sha = task[0]
            obj = json.loads(task[1], encoding='utf-8')
            title = obj.get('d:title', '')
            author = obj.get('d:author', '')
            keyword = json.loads(obj.get('d:keyword', '[]'))
            abstract = json.loads(obj.get('d:abstract', '[]'))
            total_page = obj.get('d:total_page', '')
            references = obj.get('d:references', '')
            cited_literature = obj.get('d:cited_literature', '')
            ref_detail = ''
            cit_detail = ''
            if references:
                ref_detail = json.loads(references).get('detail', '')
            if cited_literature:
                cit_detail = json.loads(cited_literature).get('detail', '')

            # ======================== 期刊论文实体数据 ===========================
            entity_data = dict()

            if title and author and keyword and abstract:
                entity_data['quality_score'] = '100'
            elif title and author and keyword:
                entity_data['quality_score'] = '80'
            elif title and author and int(total_page) > 1 and (ref_detail or cit_detail):
                entity_data['quality_score'] = '60'
            else:
                entity_data['quality_score'] = '0'

            logger.info('handle | score | use time: {} | score: {} | sha: {}'.
                        format(self.timer.use_time(), entity_data['quality_score'], sha))
            # ====================================公共字段
            # 生成sha
            entity_data['sha'] = sha
            # 生成ss ——实体
            entity_data['ss'] = '论文'
            # es ——栏目名称
            entity_data['es'] = '期刊论文'
            # 生成ws ——目标网站
            entity_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            entity_data['clazz'] = '论文_期刊论文'
            # 生成biz ——项目
            entity_data['biz'] = '文献大数据_论文'
            # 元数据版本号
            entity_data['metadata_version'] = 'V1.2.1'
            # 采集脚本版本号
            entity_data['script_version'] = 'V1.4.1'

            data_list.append(entity_data)

        logger.info('handle | check | use time: {} | count: {}'.format(self.timer.use_time(), len(task_list)))

    def run(self, row_start, row_stop):
        logger.debug('thread start')
        task_timer = timers.Timer()
        total_count = 0
        redis_field_key = row_start + ':' + row_stop
        query = "SingleColumnValueFilter('s', 'ws', =, 'substring:中国知网') AND SingleColumnValueFilter('s', 'es', =, 'substring:期刊论文') AND SingleColumnValueFilter('d', 'metadata_version', =, 'substring:V1', true, true)"
        columns = ['s:ws', 's:es', 'd:script_version', 'd:metadata_version', 'd:title', 'd:author', 'd:abstract',
                   'd:keyword', 'd:total_page', 'd:references', 'd:cited_literature', 'd:url']
        # get last start_key from redis;
        redis_value = self.redis_obj.hget('check_start', redis_field_key)
        if redis_value:
            redis_values = redis_value.split('|')
            first_key = redis_values[0]
            total_count = int(redis_values[1])
        else:
            first_key = row_start

        # 单线程无限循环
        while True:
            # 获取任务
            logger.debug('task start')
            task_timer.start()
            # task_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER, count=1,
            #                              lockname=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER_LOCK)
            # task = self.dao.get_one_task_from_redis(key=config.REDIS_QIKAN_PAPER)

            task_list = self.hbase_obj.scan_from_hbase(table='ss_paper', row_start=first_key, row_stop=row_stop,
                                                       query=query, columns=columns)
            if task_list:
                total_count += len(task_list)
                first_key = task_list[0][0]
                # 将起始行键和处理总量存入redis中
                self.redis_obj.hset('check_start', redis_field_key,
                                    "{}|{}".format(first_key, total_count))
                # 创建数据存储列表
                data_list = []

                try:
                    # 获取字段值存入字典并返回sha
                    self.handle(task_list=task_list, data_list=data_list)
                    # 保存数据到Hbase
                    if not data_list:
                        logger.error(
                            'task end | task failed | use time: {} | count: {} | key: {} | No data'.
                                format(task_timer.use_time(), len(task_list), first_key))
                    elif 'sha' not in data_list[-1]:
                        logger.error(
                            'task end | task failed | use time: {} | count: {} | key: {} | Data Incomplete'.
                                format(task_timer.use_time(), len(task_list), first_key))
                    else:
                        # 存储数据
                        success = self.dao.save_data_to_hbase(data=data_list)

                        if not success:
                            logger.error(
                                'task end | task failed | use time: {} | count: {} | key: {}'.
                                    format(task_timer.use_time(), len(task_list), first_key))
                except Exception as e:
                    logger.exception(str(traceback.format_exc()))
                    logger.error(
                        'task end | task failed | use time: {} | count: {} | key: {} | {}'.
                            format(task_timer.use_time(), len(task_list), first_key, e))

                row_start = task_list[-1][0]
                first_key = row_start[:39] + chr(ord(row_start[39:]) + 1)
                logger.info(
                    'task end | task success | use time: {} | count: {}'.
                        format(task_timer.use_time(), len(task_list), first_key))
            else:
                logger.info('task | hbase库中已无任务')
                break


def start(row_start, row_stop, hostname):
    try:
        main = CheckerMain(hostname)
        main.run(row_start, row_stop)
    except:
        logger.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    if (len(sys.argv)) < 3:
        print("Usage: {} <row_start> <row_stop> <hostname>".format(sys.argv[0]))
        exit(1)

    logger.info('====== The Start! ======')
    row_start = sys.argv[1]
    row_stop = sys.argv[2]
    hostname = sys.argv[3]

    total_timer = timers.Timer()
    total_timer.start()
    start(row_start, row_stop, hostname)
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is {} ======' % (total_timer.use_time()))
