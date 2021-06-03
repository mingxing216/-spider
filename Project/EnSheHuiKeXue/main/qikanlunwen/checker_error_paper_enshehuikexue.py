# -*-coding:utf-8-*-

"""

"""
# import gevent
# from gevent import monkey
# monkey.patch_all()
import os
import sys
import json
import base64
import time
import traceback
from io import BytesIO
from fitz import fitz

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Project.EnSheHuiKeXue.service import service
from Project.EnSheHuiKeXue.dao import dao
from Project.EnSheHuiKeXue import config
from Log import logging
from Utils import timers, hbase_pool, redis_pool
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME

LOG_FILE_DIR = 'EnSheHuiKeXue'  # LOG日志存放路径
LOG_NAME = '论文_check'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseChecher(object):
    def __init__(self):
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           host=SPI_HOST, port=SPI_PORT, user=SPI_USER, pwd=SPI_PASS, db=SPI_NAME,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class CheckerMain(BaseChecher):
    def __init__(self, hostname):
        super().__init__()
        self.timer = timers.Timer()
        self.pdf_timer = timers.Timer()
        # redis对象
        self.redis_obj = redis_pool.RedisPoolUtils(10, 3)
        # hbase对象
        self.hbase_obj = hbase_pool.HBasePool(host=hostname, logging=logger)

    def is_valid_pdf_bytes(self, content):
        b_valid = True
        try:
            with fitz.open(stream=BytesIO(content), filetype="pdf") as doc:
                if not doc.isPDF:
                    b_valid = False

                if doc.pageCount < 1:
                    b_valid = False

        except Exception:
            return

        return b_valid

    def handle(self, sha, task, data_dict):
        self.timer.start()
        task_obj = task
        title = task_obj.get('d:title', '')
        author = task_obj.get('d:author', '')
        keyword = json.loads(task_obj.get('d:keyword', '[]'))
        abstract = json.loads(task_obj.get('d:abstract', '[]'))
        total_page = json.loads(task_obj.get('d:journal_information', '{}')).get('total_page', '')
        if total_page:
            try:
                total_page = int(total_page)
            except Exception:
                logger.error('checker | 页码错误, 设置为0, {}'.format(total_page))
                total_page = 0
        else:
            total_page = 0
        classification_code = json.loads(task_obj.get('d:classification_code', '{}')).get('code', '')
        ref_detail = json.loads(task_obj.get('d:references', '{}')).get('detail', '')
        cit_detail = json.loads(task_obj.get('d:cited_literature', '{}')).get('detail', '')

        # ======================== 期刊论文实体数据 ===========================

        if title and author and keyword and abstract and classification_code:
            data_dict['quality_score'] = '100'
        elif title and author and keyword and classification_code:
            data_dict['quality_score'] = '80'
        elif title and author and (total_page > 1) and (ref_detail or cit_detail):
            data_dict['quality_score'] = '60'
        elif title and author and keyword and abstract:
            data_dict['quality_score'] = '40'
        elif title and author and keyword:
            data_dict['quality_score'] = '20'
        else:
            data_dict['quality_score'] = '0'

        logger.info('checker | score | use time: {} | score: {} | sha: {}'.
                    format(self.timer.use_time(), data_dict['quality_score'], sha))

        self.pdf_timer.start()
        # 获取关联文档实体中的全文主键
        # document_sha = json.loads(task_obj.get('d:rela_document', '{}')).get('sha', '')
        doc_sha = json.loads(task_obj.get('d:rela_document', '{}')).get('sha', '')
        if not doc_sha:
            logger.error('fulltext | 无关联文档 | use time: {} | none | sha: {}'.
                         format(self.pdf_timer.use_time(), sha))
            data_dict['has_fulltext'] = 'None'
        else:
            # 获取文档实体数据
            doc_columns = ['d:label_obj']
            doc_data = self.hbase_obj.get_one_data_from_hbase('ss_document', doc_sha, doc_columns)
            if not doc_data:
                logger.error('fulltext | 无文档实体 | use time: {} | none | sha: {}'.
                             format(self.pdf_timer.use_time(), sha))
                data_dict['has_fulltext'] = 'None'
            else:
                # 获取全文主键
                fulltext_sha = json.loads(doc_data.get('d:label_obj', '{}')).get('全部', '[]')[0].get('sha', '')
                if not fulltext_sha:
                    logger.error('fulltext | 无关联全文 | use time: {} | none | sha: {}'.
                                 format(self.pdf_timer.use_time(), sha))
                    data_dict['has_fulltext'] = 'None'
                else:
                    fulltext_columns = ['o:content_type', 'o:length', 'm:content']
                    fulltext_data = self.hbase_obj.get_one_data_from_hbase('media:document', fulltext_sha, fulltext_columns)
                    if not fulltext_data:
                        logger.error('fulltext | 无全文 | use time: {} | none | sha: {}'.
                                     format(self.pdf_timer.use_time(), sha))
                        data_dict['has_fulltext'] = 'None'
                    else:
                        content_type = fulltext_data.get('o:content_type', '')
                        if 'pdf' in content_type:
                            fulltext = fulltext_data.get('m:content', '')
                            b_fulltext = base64.b64decode(fulltext)
                            # 检测PDF文件
                            is_value = self.is_valid_pdf_bytes(b_fulltext)
                            if is_value is None:
                                logger.error('fulltext | 检测PDF文件出错 | use time: {} | sha: {}'.
                                             format(self.pdf_timer.use_time(), fulltext_sha))
                                data_dict['has_fulltext'] = 'None'
                            elif not is_value:
                                # 更新种子错误信息
                                logger.error('fulltext | not PDF | use time: {} | sha: {}'.
                                             format(self.pdf_timer.use_time(), fulltext_sha))
                                data_dict['has_fulltext'] = 'None'
                            else:
                                data_dict['has_fulltext'] = 'PDF'

                        elif 'text' in content_type:
                            data_dict['has_fulltext'] = 'HTML'
                        else:
                            data_dict['has_fulltext'] = content_type

        # ====================================公共字段
        # 生成sha
        data_dict['sha'] = sha
        # 生成ss ——实体
        data_dict['ss'] = '论文'
        # 生成clazz ——层级关系
        data_dict['clazz'] = task_obj.get('s:clazz', '')
        # 生成ws ——目标网站
        data_dict['ws'] = task_obj.get('s:ws', '')
        # 生成biz ——项目
        data_dict['biz'] = '文献大数据_论文'
        # 更新责任人
        data_dict['modified_by'] = '张明星'
        # 元数据版本号
        data_dict['metadata_version'] = 'V1.1.1'
        # 采集脚本版本号
        data_dict['script_version'] = 'V1.3.1'

        logger.info('handle | check | use time: {}'.format(self.timer.use_time()))

    def run(self):
        logger.debug('thread start')
        task_timer = timers.Timer()

        columns = ['s:ws', 's:es', 's:clazz', 'd:script_version', 'd:metadata_version', 'd:title', 'd:author', 'd:abstract',
                   'd:keyword', 'd:journal_information', 'd:classification_code', 'd:rela_document', 'd:references', 'd:cited_literature', 'd:url']

        with open('/opt/Log/Temp/ensheke_error_sha.log', 'r') as f:
            first_key_list = f.readlines()
            for first_key in first_key_list:
                first_key = first_key.replace('\n', '')
                # 获取任务
                logger.debug('task start')
                task_timer.start()

                task = self.hbase_obj.get_one_data_from_hbase(table='ss_paper', row_key=first_key, columns=columns)
                if task is None:
                    logger.error('task | hbase库row任务失败, 等待30s重新获取')
                    time.sleep(30)
                    continue

                elif not task:
                    logger.info('task | hbase库中已无任务')
                    break

                else:
                    # 创建数据存储列表
                    data_dict = {}

                    try:
                        # 获取字段值存入字典并返回sha
                        self.handle(sha=first_key, task=task, data_dict=data_dict)
                        # 保存数据到Hbase
                        if not data_dict:
                            logger.error(
                                'task end | task failed | use time: {} | count: {} | key: {} | No data'.
                                    format(task_timer.use_time(), len(task), first_key))
                        elif 'sha' not in data_dict:
                            logger.error(
                                'task end | task failed | use time: {} | count: {} | key: {} | Data Incomplete'.
                                    format(task_timer.use_time(), len(task), first_key))
                        else:
                            # 存储数据
                            success = self.dao.save_data_to_hbase(data=data_dict)

                            if not success:
                                logger.error(
                                    'task end | task failed | use time: {} | count: {} | key: {}'.
                                        format(task_timer.use_time(), len(task), first_key))
                    except Exception as e:
                        logger.exception(str(traceback.format_exc()))
                        logger.error(
                            'task end | task failed | use time: {} | count: {} | key: {} | {}'.
                                format(task_timer.use_time(), len(task), first_key, e))

                    logger.info(
                        'task end | task success | use time: {} | count: {} | key: {}'.
                            format(task_timer.use_time(), len(task), first_key))

def start(hostname):
    try:
        main = CheckerMain(hostname)
        main.run()
    except:
        logger.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    hostname = sys.argv[1]

    logger.info('====== The Start! ======')
    total_timer = timers.Timer()
    total_timer.start()
    start(hostname)
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is {} ======'.format(total_timer.use_time()))
