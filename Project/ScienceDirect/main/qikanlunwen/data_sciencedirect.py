# -*- coding:utf-8 -*-

# import gevent
# from gevent import monkey
# monkey.patch_all()
import os
import sys
import hashlib
import json
import random
import re
import time
import traceback
import requests
# from contextlib import closing
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from PyPDF4 import PdfFileReader
from fitz import fitz

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Project.ScienceDirect.middleware import download_middleware
from Project.ScienceDirect.service import service
from Project.ScienceDirect.dao import dao
from Project.ScienceDirect import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import user_pool, timers
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY, LANG_API, SPI_HOST, SPI_PORT, SPI_USER, SPI_PASS, SPI_NAME

LOG_FILE_DIR = 'ScienceDirect'  # LOG日志存放路径
LOG_NAME = '英文期刊论文_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        # 下载中间件
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           host=SPI_HOST, port=SPI_PORT, user=SPI_USER, pwd=SPI_PASS, db=SPI_NAME,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        self.lang_api = 'http://localhost:9008/detect'
        self.timer = timers.Timer()
        self.s = requests.Session()

    # 检测PDF文件正确性
    # @staticmethod
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

    # 获取文档实体字段
    def document(self, pdf_dict, data_list):
        logger.debug('document | 开始获取内容')
        self.timer.start()
        page_pdf_url = pdf_dict.get('url')
        # 获取页面响应
        page_pdf_resp = self.download.get_resp(url=page_pdf_url, s=self.s, method='GET')
        if page_pdf_resp is None:
            logger.error('downloader | 论文全文跳转页响应失败, url: {}'.format(page_pdf_url))
            return
        if not page_pdf_resp['data']:
            logger.error('downloader | 论文全文跳转页响应失败, url: {}'.format(page_pdf_url))
            return
        page_pdf_text = page_pdf_resp['data'].text

        real_pdf_url = self.server.get_real_pdf_url(page_pdf_text)
        if real_pdf_url:
            pdf_resp = self.download.get_resp(url=real_pdf_url, s=self.s, method='GET')
            if pdf_resp is None:
                logger.error('downloader | 论文全文页响应失败, url: {}'.format(real_pdf_url))
                return
            if not pdf_resp['data']:
                logger.error('downloader | 论文全文页响应失败, url: {}'.format(real_pdf_url))
                return

            if 'text' in pdf_resp['data'].headers.get('Content-Type') or 'html' in pdf_resp['data'].headers.get('Content-Type'):
                # 更新种子错误信息
                msg = 'Content-Type error: {}'.format(pdf_resp['data'].headers['Content-Type'])
                logger.warning('document | {} | url: {}'.format(msg, page_pdf_url))
                data_dict = {'url': pdf_dict['relEsse']['url']}
                self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='sciencedirect', es='期刊论文', msg=msg)
                return

            else:
                # 内存中读写
                bytes_container = BytesIO()
                # 断点续爬，重试3次
                for retry_count in range(3):
                    # 判断内容获取是否完整
                    if pdf_resp['data'].raw.tell() >= int(pdf_resp['data'].headers.get('Content-Length', 0)):
                        # 获取二进制内容
                        bytes_container.write(pdf_resp['data'].content)
                        logger.info('document | 获取内容完整 | use time: {} | length: {}'.format(self.timer.use_time(),
                                                                                         len(bytes_container.getvalue())))
                        # pdf_content += pdf_resp.content
                        break
                    else:
                        # 获取二进制内容
                        bytes_container.write(pdf_resp['data'].content)
                        logger.warning(
                            'document | 获取内容不完整, 重新下载 | use time: {} | length: {}'.format(self.timer.use_time(),
                                                                                  len(bytes_container.getvalue())))
                        # # 存储文档种子
                        # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
                        # 请求头增加参数
                        ranges = 'bytes=%d-' % len(bytes_container.getvalue())
                        # 断点续传
                        pdf_resp = self.download.get_resp(url=real_pdf_url, method='GET', s=self.s, ranges=ranges)
                        if pdf_resp is None:
                            logger.error('downloader | 论文全文页响应失败, url: {}'.format(real_pdf_url))
                            return
                        if not pdf_resp['data']:
                            logger.error('downloader | 论文全文页响应失败, url: {}'.format(real_pdf_url))
                            return

                        continue
                else:
                    # LOGGING.info('handle | 获取内容不完整 | use time: {} |
                    # length: {}'.format('%.3f' % (time.time() - start_time),
                    # len(bytes_container.getvalue())))
                    # 更新种子错误信息
                    msg = 'Content-Length error: {}/{}'.format(len(bytes_container.getvalue()),
                                                               pdf_resp['data'].headers.get('Content-Length', 0))
                    logger.error('document | download failed | {} | url: {}'.format(msg, page_pdf_url))
                    data_dict = {'url': pdf_dict['relEsse']['url']}
                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='sciencedirect', es='期刊论文', msg=msg)
                    return

                # 获取二进制内容
                pdf_content = bytes_container.getvalue()
                pdf_length = len(pdf_content)
                logger.debug('document | 结束获取内容')

                # 检测PDF文件
                is_value = self.is_valid_pdf_bytes(pdf_content)
                if is_value is None:
                    msg = '检测PDF文件出错'
                    logger.error('document | {} | url: {}'.format(msg, page_pdf_url))
                    data_dict = {'url': pdf_dict['relEsse']['url']}
                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='sciencedirect', es='期刊论文', msg=msg)
                    return

                if not is_value:
                    # 更新种子错误信息
                    msg = 'not PDF'
                    logger.error('document | {} | url: {}'.format(msg, page_pdf_url))
                    data_dict = {'url': pdf_dict['relEsse']['url']}
                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='sciencedirect', es='期刊论文', msg=msg)
                    return

                # 存储全文
                content_type = 'application/pdf'
                succ = self.dao.save_media_to_hbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict,
                                                    type='document', length=pdf_length, contype=content_type)
                if not succ:
                    return

            # 文档数据存储字典
            doc_entity = dict()
            # 获取标题
            doc_entity['title'] = pdf_dict['biz_title']
            # 文档内容
            doc_entity['label_obj'] = self.server.get_media(media_data=pdf_dict, media_key='document', ss='document',
                                                            format='PDF', size=pdf_length)
            # 获取来源网站
            doc_entity['source_website'] = ""
            # 关联论文
            doc_entity['rela_paper'] = pdf_dict['rel_esse']

            # ===================公共字段
            # url
            doc_entity['url'] = pdf_dict['url']
            # 生成key
            doc_entity['key'] = pdf_dict['key']
            # 生成sha
            doc_entity['sha'] = hashlib.sha1(doc_entity['key'].encode('utf-8')).hexdigest()
            # 生成ss ——实体
            doc_entity['ss'] = '文档'
            # 生成es ——栏目名称
            doc_entity['es'] = '期刊论文'
            # 生成ws ——目标网站
            doc_entity['ws'] = 'sciencedirect'
            # 生成clazz ——层级关系
            doc_entity['clazz'] = '文档_论文文档'
            # 生成biz ——项目
            doc_entity['biz'] = '文献大数据_论文'
            # 生成ref
            doc_entity['ref'] = ''
            # 采集责任人
            doc_entity['creator'] = '张明星'
            # 更新责任人
            doc_entity['modified_by'] = ''
            # 采集服务器集群
            doc_entity['cluster'] = 'crawler'
            # 元数据版本号
            doc_entity['metadata_version'] = 'V1.3'
            # 采集脚本版本号
            doc_entity['script_version'] = 'V1.3'
            # 文档实体存入列表
            data_list.append(doc_entity)

            return True

    def handle(self, task_data, data_list):
        # print(task_data)
        url = task_data.get('url')
        try:
            _id= url.split('/')[-1]
        except:
            return
        # print(id)
        key = 'sciencedirect|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()

        # 获取详情页
        profile_resp = self.download.get_resp(url=url, method='GET', s=self.s)
        if profile_resp is None:
            logger.error('downloader | 论文详情页响应失败, url: {}'.format(url))
            return
        if not profile_resp['data']:
            logger.error('downloader | 论文详情页响应失败, url: {}'.format(url))
            return

        profile_text = profile_resp['data'].text
        # with open('profile.html', 'w') as f:
        #     f.write(profile_text)

        # ========================== 获取实体 ============================
        # 创建数据存储字典
        paper_entity = dict()
        # 获取标题
        paper_entity['title'] = self.server.get_paper_title(profile_text)
        # # 获取作者
        # paper_entity['author'] = self.server.get_more_value(profile_text, '作者')
        # # ISSN
        # paper_entity['issn'] = self.server.get_normal_value(profile_text, '印刷版ISSN')
        # paper_entity['e_issn'] = self.server.get_normal_value(profile_text, '电子版ISSN')
        # # DOI
        # paper_entity['doi'] = {}
        # doi = self.server.get_normal_value(profile_text, 'DOI')
        # doi_url = self.server.get_full_link(profile_text, '全文链接')
        # if doi:
        #     save_data['doi']['doi'] = doi
        #     save_data['doi']['doi_url'] = doi_url
        #     save_data['source_url'] = ""
        # else:
        #     # 全文链接
        #     save_data['source_url'] = doi_url
        # # 获取期刊信息
        # paper_entity['journal_information'] = {}
        # paper_entity['journal_information']['name'] = self.server.get_normal_value(profile_text, '期刊名称')
        # paper_entity['journal_information']['year'] = self.server.get_normal_value(profile_text, '出版年度')
        # paper_entity['journal_information']['volume'] = self.server.get_normal_value(profile_text, '卷号')
        # paper_entity['journal_information']['issue'] = self.server.get_normal_value(profile_text, '期号')
        # pages = self.server.get_normal_value(profile_text, '页码')
        # if pages:
        #     if '-' in pages:
        #         paper_entity['journal_information']['start_page'] = re.findall(r"(.*)-", pages)[0]
        #         paper_entity['journal_information']['end_page'] = re.findall(r"-(.*)", pages)[0]
        #         paper_entity['journal_information']['total_page'] = ""
        #     else:
        #         paper_entity['journal_information']['start_page'] = ""
        #         paper_entity['journal_information']['end_page'] = ""
        #         paper_entity['journal_information']['total_page'] = pages
        # else:
        #     paper_entity['journal_information']['start_page'] = ""
        #     paper_entity['journal_information']['end_page'] = ""
        #     paper_entity['journal_information']['total_page'] = ""
        # # 语种
        # paper_entity['language'] = self.server.get_normal_value(profile_text, '语种')
        # # 出版社
        # paper_entity['publisher'] = self.server.get_normal_value(profile_text, '出版社')
        # # 获取摘要
        # paper_entity['abstract'] = []
        # abstract_text = self.server.get_abstract_value(profile_text, '摘要')
        # if abstract_text:
        #     abstract = {}
        #     abstract['text'] = abstract_text
        #     form_data = {'q': abstract['text']}
        #     try:
        #         lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5,10))
        #         lang = lang_resp.json().get('responseData').get('language')
        #     except:
        #         return
        #     abstract['lang'] = lang
        #     paper_entity['abstract'].append(abstract)
        # en_abstract_text = self.server.get_normal_value(profile_text, '英文摘要')
        # if en_abstract_text:
        #     en_abstract = {}
        #     en_abstract['text'] = en_abstract_text
        #     form_data = {'q': en_abstract['text']}
        #     try:
        #         lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5,10))
        #         lang = lang_resp.json().get('responseData').get('language')
        #     except:
        #         return
        #     en_abstract['lang'] = lang
        #     paper_entity['abstract'].append(en_abstract)
        # # 获取关键词
        # paper_entity['keyword'] = []
        # keyword_text = self.server.get_keyword_value(profile_text, '关键词')
        # if keyword_text:
        #     keyword = {}
        #     keyword['text'] = keyword_text
        #     form_data = {'q': keyword['text']}
        #     try:
        #         lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5,10))
        #         lang = lang_resp.json().get('responseData').get('language')
        #     except:
        #         return
        #     keyword['lang'] = lang
        #     paper_entity['keyword'].append(keyword)
        # en_keyword_text = self.server.get_en_keyword_value(profile_text, '英文关键词')
        # if en_keyword_text:
        #     en_keyword = {}
        #     en_keyword['text'] = en_keyword_text
        #     form_data = {'q': en_keyword['text']}
        #     try:
        #         lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5,10))
        #         lang = lang_resp.json().get('responseData').get('language')
        #     except:
        #         return
        #     en_keyword['lang'] = lang
        #     paper_entity['keyword'].append(en_keyword)
        # # 获取作者单位
        # paper_entity['author_affiliation'] = self.server.get_author_affiliation(profile_text, '作者单位')
        # # 关联期刊
        # qikan_url = task_data.get('journalUrl')
        # qikan_id = re.findall(r"id=(\w+)$", qikan_url)[0]
        # qikan_key = '哲学社会科学外文OA资源数据库|' + qikan_id
        # qikan_sha = hashlib.sha1(qikan_key.encode('utf-8')).hexdigest()
        # paper_entity['rela_journal'] = self.server.rela_journal(qikan_url, qikan_key, qikan_sha)
        # 获取关联文档
        pdf_url = task_data.get('pdfUrl')
        if not pdf_url:
            paper_entity['rela_document'] = {}

        else:
            doc_key = key
            doc_sha = hashlib.sha1(doc_key.encode('utf-8')).hexdigest()
            doc_url = pdf_url
            paper_entity['rela_document'] = self.server.rela_entity(doc_url, doc_key, doc_sha, '文档')

            pdf_dict = dict()
            pdf_dict['url'] = doc_url
            pdf_dict['key'] = doc_key
            pdf_dict['id'] = _id
            pdf_dict['biz_title'] = paper_entity['title']
            pdf_dict['rel_esse'] = self.server.rela_entity(url, key, sha, '论文')
            pdf_dict['rel_pics'] = paper_entity['rela_document']

            # 存储文档实体及文档本身
            suc = self.document(pdf_dict=pdf_dict, data_list=data_list)
            if not suc:
                return

        # ======================公共字段
        # url
        paper_entity['url'] = url
        # 生成key
        paper_entity['key'] = key
        # 生成sha
        paper_entity['sha'] = sha
        # 生成ss ——实体
        paper_entity['ss'] = '论文'
        # es ——栏目名称
        paper_entity['es'] = '期刊论文'
        # 生成ws ——目标网站
        paper_entity['ws'] = 'sciencedirect'
        # 生成clazz ——层级关系
        paper_entity['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        paper_entity['biz'] = '文献大数据_论文'
        # 生成ref
        paper_entity['ref'] = ''
        # 采集责任人
        paper_entity['creator'] = '张明星'
        # 更新责任人
        paper_entity['modified_by'] = ''
        # 采集服务器集群
        paper_entity['cluster'] = 'crawler'
        # 元数据版本号
        paper_entity['metadata_version'] = 'V1.3'
        # 采集脚本版本号
        paper_entity['script_version'] = 'V1.3'
        # 论文实体存入列表
        data_list.append(paper_entity)

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
            # task = self.dao.get_one_task_from_redis(key=config.REDIS_SCIENCEDIRECT_PAPER)
            task = '{"url": "https://www.sciencedirect.com/science/article/pii/S0016787805800549", "pdfUrl": "https://www.sciencedirect.com/science/article/pii/S0016787805800549/pdfft?md5=5dbd49b134566eba897ec19c82129553&pid=1-s2.0-S0016787805800549-main.pdf", "type": "", "rights": "Full text access", "journalColumn": "", "journalUrl": "https://www.sciencedirect.com/journal/proceedings-of-the-geologists-association", "journalId": "proceedings-of-the-geologists-association", "year": "2005", "vol": "116", "issue": "3", "sha": "27dd9c73dd282956355b076da34512d37d8cac56"}'
            if not task:
                logger.info('task | 队列中已无任务')

            else:
                # 创建数据存储列表
                data_list = []
                # json数据类型转换
                task_data = json.loads(task)
                sha = task_data['sha']
                try:
                    # 获取字段值存入字典并返回sha
                    self.handle(task_data=task_data, data_list=data_list)
                    # 保存数据到Hbase
                    if not data_list:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | No data.'.format(task_timer.use_time()))
                        continue
                    if 'sha' not in data_list[-1]:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | Data Incomplete.'.format(task_timer.use_time()))
                        continue
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=data_list)

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
    tpool = ThreadPoolExecutor(max_workers=config.THREAD_NUM)
    for i in range(config.THREAD_NUM):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    total_timer = timers.Timer()
    total_timer.start()
    # process_start()
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is {} ======'.format(total_timer.use_time()))
