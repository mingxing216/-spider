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
import traceback
from io import BytesIO
from fitz import fitz

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from Log import logging
from Utils import timers, hbase_pool, redis_pool
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME

LOG_FILE_DIR = 'SheHuiKeXue'  # LOG日志存放路径
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
        self.redis_obj = redis_pool.RedisPoolUtils(10, 2)
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

    def handle(self, task_list, data_list):
        paper_doc_dict = {}
        doc_entity_dict = {}
        doc_sha_list = []
        self.timer.start()
        for task in task_list:
            sha = task[0]
            task_obj = task[1]
            doc_sha = json.loads(task_obj.get('d:rela_document', '{}')).get('sha', '')
            paper_doc_dict[sha] = doc_sha
            if doc_sha:
                doc_sha_list.append(doc_sha)

        columns = ['d:label_obj']
        doc_data_list = self.hbase_obj.get_datas_from_hbase('ss_document', doc_sha_list, columns)
        for doc_data in doc_data_list:
            doc_entity_dict[doc_data[0]] = doc_data[1]

        for task in task_list:
            sha = task[0]
            task_obj = task[1]
            title = task_obj.get('d:title', '')
            author = task_obj.get('d:author', '')
            keyword = json.loads(task_obj.get('d:keyword', '{}')).get('text', '')
            abstract = json.loads(task_obj.get('d:abstract', '{}')).get('text', '')
            total_page = json.loads(task_obj.get('d:journal_information', '{}')).get('total_page', '')
            if total_page:
                total_page = int(total_page)
            else:
                total_page = 0
            classification_code = json.loads(task_obj.get('d:classification_code', '{}')).get('code', '')
            ref_detail = json.loads(task_obj.get('d:references', '{}')).get('detail', '')
            cit_detail = json.loads(task_obj.get('d:cited_literature', '{}')).get('detail', '')

            # ======================== 期刊论文实体数据 ===========================
            entity_data = dict()

            if title and author and keyword and abstract and classification_code:
                entity_data['quality_score'] = '100'
            elif title and author and keyword and classification_code:
                entity_data['quality_score'] = '80'
            elif title and author and (total_page > 1) and (ref_detail or cit_detail):
                entity_data['quality_score'] = '60'
            else:
                entity_data['quality_score'] = '0'

            logger.info('checker | score | use time: {} | score: {} | sha: {}'.
                        format(self.timer.use_time(), entity_data['quality_score'], sha))

            self.pdf_timer.start()
            # 获取关联文档实体中的全文主键
            # document_sha = json.loads(task_obj.get('d:rela_document', '{}')).get('sha', '')
            doc_sha = paper_doc_dict[sha]
            if not doc_sha:
                logger.error('fulltext | 无关联文档 | use time: {} | none | sha: {}'.
                             format(self.pdf_timer.use_time(), sha))
                entity_data['has_fulltext'] = 'None'
            else:
                # 获取文档实体数据
                doc_data = doc_entity_dict[doc_sha]
                if not doc_data:
                    logger.error('fulltext | 无文档实体 | use time: {} | none | sha: {}'.
                                 format(self.pdf_timer.use_time(), sha))
                    entity_data['has_fulltext'] = 'None'
                else:
                    # 获取全文主键
                    fulltext_sha = json.loads(doc_data.get('d:label_obj', '{}')).get('全部', '[]')[0].get('sha', '')
                    if not fulltext_sha:
                        logger.error('fulltext | 无关联全文 | use time: {} | none | sha: {}'.
                                     format(self.pdf_timer.use_time(), sha))
                        entity_data['has_fulltext'] = 'None'
                    else:
                        columns = ['o:content_type', 'o:length', 'm:content']
                        fulltext_data = self.hbase_obj.get_one_data_from_hbase('media:document', fulltext_sha, columns)
                        if not fulltext_data:
                            logger.error('fulltext | 无全文 | use time: {} | none | sha: {}'.
                                         format(self.pdf_timer.use_time(), sha))
                            entity_data['has_fulltext'] = 'None'
                        else:
                            content_type = fulltext_data.get('o:content_type', '')
                            fulltext = fulltext_data.get('m:content', '')
                            b_fulltext = base64.b64decode(fulltext)
                            # 检测PDF文件
                            is_value = self.is_valid_pdf_bytes(b_fulltext)
                            if is_value is None:
                                logger.error('fulltext | 检测PDF文件出错 | use time: {} | sha: {}'.
                                             format(self.pdf_timer.use_time(), fulltext_sha))
                                entity_data['has_fulltext'] = 'None'
                            elif not is_value:
                                # 更新种子错误信息
                                logger.error('fulltext | not PDF | use time: {} | sha: {}'.
                                             format(self.pdf_timer.use_time(), fulltext_sha))
                                entity_data['has_fulltext'] = 'None'
                            else:
                                # # 全文数据增加content_type字段
                                # con_type = 'application/pdf'
                                # self.dao.save_content_type_to_hbase(sha=fulltext_sha, type='document', contype=con_type)
                                if 'pdf' in content_type:
                                    entity_data['has_fulltext'] = 'PDF'
                                elif 'text' in content_type:
                                    entity_data['has_fulltext'] = 'HTML'
                                else:
                                    entity_data['has_fulltext'] = content_type

            # ====================================公共字段
            # 生成sha
            entity_data['sha'] = sha
            # 生成ss ——实体
            entity_data['ss'] = '论文'
            # 生成clazz ——层级关系
            entity_data['clazz'] = task_obj.get('s:clazz', '')
            # 生成ws ——目标网站
            entity_data['ws'] = task_obj.get('s:ws', '')
            # 生成biz ——项目
            entity_data['biz'] = '文献大数据_论文'
            # 更新责任人
            entity_data['modified_by'] = '张明星'
            # 元数据版本号
            entity_data['metadata_version'] = 'V1.1.1'
            # 采集脚本版本号
            entity_data['script_version'] = 'V1.3.1'

            data_list.append(entity_data)

        logger.info('handle | check | use time: {} | count: {}'.format(self.timer.use_time(), len(task_list)))

    def run(self, row_start, row_stop):
        logger.debug('thread start')
        task_timer = timers.Timer()
        total_count = 0
        redis_field_key = row_start + ':' + row_stop
        query = "SingleColumnValueFilter('s', 'ws', =, 'substring:国家哲学社会科学学术期刊数据库') AND SingleColumnValueFilter('d', 'metadata_version', =, 'substring:V1', true, true)"
        columns = ['s:ws', 's:es', 's:clazz', 'd:script_version', 'd:metadata_version', 'd:title', 'd:author', 'd:abstract',
                   'd:keyword', 'd:journal_information', 'd:classification_code', 'd:rela_document', 'd:references', 'd:cited_literature', 'd:url']
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

            task_list = self.hbase_obj.scan_from_hbase(table='ss_paper', row_start=first_key, row_stop=row_stop,
                                                       query=query, columns=columns, limit=500)
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
    logger.info('====== Time consuming is {} ======'.format(total_timer.use_time()))
