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
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config
from Log import logging
from Utils import timers, hbase_pool, redis_pool
from settings import SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME

LOG_FILE_DIR = 'ZiRanKeXue'  # LOG日志存放路径
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
        self.redis_obj = redis_pool.RedisPoolUtils(10, 1)
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

    def handle(self, data_list):
        paper_columns = ['s:ws', 's:es', 's:clazz', 'd:script_version', 'd:metadata_version', 'd:title',
                   'd:author', 'd:abstract', 'd:keyword', 'd:journal_information', 'd:classification_code',
                   'd:rela_document', 'd:references', 'd:cited_literature', 'd:url']
        fulltext_columns = ['o:content_type', 'o:length', 'o:rel_esse', 'm:content']
        self.timer.start()
        with open('/opt/Log/Temp/ziran_error_sha.log', 'r') as f:
            full_timer = timers.Timer()
            full_timer.start()
            key_list = f.readlines()
            for key in key_list:
                fulltext_sha = key.replace('\n', '')
                fulltext_data = self.hbase_obj.get_one_data_from_hbase('media:document', fulltext_sha, fulltext_columns)
                if not fulltext_data:
                    logger.error('fulltext | 获取全文数据错误 | use time: {} | sha: {}'.
                                 format(full_timer.use_time(), fulltext_sha))
                    continue
                else:
                    paper_sha = json.loads(fulltext_data.get('o:rel_esse', '{}')).get('sha', '')
                    if not paper_sha:
                        logger.error('fulltext | 获取论文主键错误 | use time: {} | sha: {}'.
                                     format(full_timer.use_time(), fulltext_sha))
                        continue
                    else:
                        paper_data = self.hbase_obj.get_one_data_from_hbase('ss_paper', paper_sha, paper_columns)
                        if not paper_data:
                            logger.error('fulltext | 获取论文数据错误 | use time: {} | sha: {}'.
                                         format(full_timer.use_time(), fulltext_sha))
                            continue
                        else:
                            task_obj = paper_data
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
                                        format(self.timer.use_time(), entity_data['quality_score'], paper_sha))

                            self.pdf_timer.start()
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
                                # 全文数据增加content_type字段
                                con_type = 'application/pdf'
                                self.dao.save_content_type_to_hbase(sha=fulltext_sha, type='document', contype=con_type)
                                if not content_type:
                                    entity_data['has_fulltext'] = 'PDF'
                                else:
                                    if 'pdf' in content_type:
                                        entity_data['has_fulltext'] = 'PDF'
                                    elif 'text' in content_type:
                                        entity_data['has_fulltext'] = 'HTML'
                                    else:
                                        entity_data['has_fulltext'] = content_type

                # ====================================公共字段
                # 生成sha
                entity_data['sha'] = paper_sha
                # 生成ss ——实体
                entity_data['ss'] = '论文'
                # 生成clazz ——层级关系
                entity_data['clazz'] = task_obj.get('s:clazz', '')
                # 生成ws ——目标网站
                entity_data['ws'] = '国家自然科学基金委员会'
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

    def run(self):
        logger.debug('thread start')
        task_timer = timers.Timer()
        # 获取任务
        logger.debug('task start')
        task_timer.start()

        # 创建数据存储列表
        data_list = []
        try:
            # 获取字段值存入字典并返回sha
            self.handle(data_list=data_list)
            # 保存数据到Hbase
            if not data_list:
                logger.error(
                    'task end | task failed | use time: {} | count: {} | No data'.
                        format(task_timer.use_time(), len(data_list)))
            elif 'sha' not in data_list[-1]:
                logger.error(
                    'task end | task failed | use time: {} | count: {} | Data Incomplete'.
                        format(task_timer.use_time(), len(data_list)))
            else:
                # 存储数据
                success = self.dao.save_data_to_hbase(data=data_list)
                if not success:
                    logger.error(
                        'task end | task failed | use time: {} | count: {}'.
                            format(task_timer.use_time(), len(data_list)))
        except Exception as e:
            logger.exception(str(traceback.format_exc()))
            logger.error(
                'task end | task failed | use time: {} | count: {} | {}'.
                    format(task_timer.use_time(), len(data_list), e))

        logger.info(
            'task end | task success | use time: {} | count: {}'.
                format(task_timer.use_time(), len(data_list)))


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
