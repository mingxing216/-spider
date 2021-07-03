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
        self.toc_url = 'https://www.sciencedirect.com/sdfe/arp/pii/{}/toc'
        self.refer_url = 'https://www.sciencedirect.com/sdfe/arp/pii/{}/references?entitledToken={}'
        self.cited_url = 'https://www.sciencedirect.com/sdfe/arp/pii/{}/citingArticles?creditCardPurchaseAllowed=true&preventTransactionalAccess=false&preventDocumentDelivery=true'
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
        if page_pdf_resp['status'] == 404:
            return True
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

    def img_download(self, img_dict):
        # 获取图片响应
        media_resp = self.download.get_resp(url=img_dict['url'], method='GET', s=self.s)
        if media_resp is None:
            return
        if media_resp['status'] == 404:
            return True
        if not media_resp['data']:
            logger.error('downloader | 图片响应失败, url: {}'.format(img_dict['url']))
            return

        # media_resp.encoding = media_resp.apparent_encoding
        img_content = media_resp['data'].content
        # 存储图片
        content_type = 'image/jpeg'
        succ = self.dao.save_media_to_hbase(media_url=img_dict['url'], content=img_content, item=img_dict,
                                            type='image', contype=content_type)
        if not succ:
            return
        else:
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
        if not paper_entity['title']:
            logger.error('service | 无标题')
            return
        # 获取作者
        paper_entity['author'] = self.server.get_author(profile_text)
        # 获取作者单位
        paper_entity['author_affiliation'] = self.server.get_affiliation(profile_text)
        # 数字对象标识符
        paper_entity['doi'] = {}
        doi_url = self.server.get_doi(profile_text)
        if doi_url:
            paper_entity['doi']['doi_url'] = doi_url
            paper_entity['doi']['doi'] = doi_url.replace('https://doi.org/', '')
        # 获取摘要
        paper_entity['abstract'] = []
        abstract = self.server.get_paper_abstract(profile_text)
        if abstract:
            ab_dict = {}
            ab_dict['text'] = abstract
            ab_dict['lang'] = 'en'
            paper_entity['abstract'].append(ab_dict)
        # 获取关键词
        paper_entity['keyword'] = []
        keywords = self.server.get_paper_keyword(profile_text)
        if keywords:
            kw_dict = {}
            kw_dict['text'] = keywords
            kw_dict['lang'] = 'en'
            paper_entity['keyword'].append(kw_dict)
        # 获取语种
        paper_entity['language'] = 'en'
        # 期刊名称
        paper_entity['journal_name'] = self.server.get_journal_name(profile_text)
        # 所属期刊栏目
        paper_entity['journal_column'] = task_data.get('journalColumn', '')
        # 论文类型
        paper_entity['type'] = []
        type_text =  task_data.get('type', '')
        if type_text:
            type_dict = {}
            type_dict['text'] = type_text
            type_dict['lang'] = 'en'
            type_dict['type'] = 'sciencedirect'
            paper_entity['type'].append(type_dict)
        # 权限
        paper_entity['rights'] = task_data.get('rights', '')
        journal_info = self.server.get_journal_info(profile_text)
        # 年
        paper_entity['year'] = journal_info.get('year', '')
        # 卷号
        paper_entity['volume'] = journal_info.get('vol', '')
        # 期号
        paper_entity['issue'] = journal_info.get('issue', '')
        # 获取所在页码
        pages = journal_info.get('pages', '')
        if not pages:
            paper_entity['start_page'] = ''
            paper_entity['end_page'] = ''
        else:
            if '-' in pages:
                page_list = pages.split('-')
                paper_entity['start_page'] = page_list[0]
                paper_entity['end_page'] = page_list[1]
            else:
                paper_entity['start_page'] = pages
                paper_entity['end_page'] = ''
        # 日期
        paper_entity['date'] = journal_info.get('date', '')
        # 参考文献
        paper_entity['references'] = self.server.get_refer(profile_text, self.refer_url, _id, self.download, self.s)
        # 引证文献
        paper_entity['cited_literature'] = self.server.get_cited(self.cited_url, _id, self.download, self.s)
        # 关联期刊
        qikan_url = task_data.get('journalUrl')
        qikan_id = task_data.get('journalId')
        qikan_key = 'sciencedirect|' + qikan_id
        qikan_sha = hashlib.sha1(qikan_key.encode('utf-8')).hexdigest()
        paper_entity['rela_journal'] = self.server.rela_entity(qikan_url, qikan_key, qikan_sha, '期刊')
        # 获取目录、组图
        toc_url = self.toc_url.format(_id)
        toc_resp = self.download.get_resp(url=toc_url, method='GET', s=self.s)
        if toc_resp is None:
            logger.error('downloader | 论文json页响应失败, url: {}'.format(toc_url))
            return
        if not toc_resp['data']:
            logger.error('downloader | 论文json页响应失败, url: {}'.format(toc_url))
            return

        toc_text = toc_resp['data'].json()

        # 目录
        paper_entity['catalog'] = []
        catalog = self.server.get_catalog(toc_text)
        if catalog:
            catalog_dict = {}
            catalog_dict['text'] = catalog
            catalog_dict['lang'] = 'en'
            paper_entity['catalog'].append(catalog_dict)
        # 关联组图
        pic_datas = self.server.get_pic_url(toc_text, paper_entity['title'])
        if not pic_datas:
            paper_entity['rela_pics'] = {}
        else:
            paper_entity['rela_pics'] = self.server.rela_entity(url, key, sha, '组图')
            # 组图实体
            pics = {}
            # 标题
            pics['title'] = paper_entity['title']
            # 组图内容
            pics['label_obj'] = self.server.get_pics(pic_datas, 'picture', 'image')
            # 关联论文
            pics['rela_paper'] = self.server.rela_entity(url, key, sha, '论文')
            # url
            pics['url'] = url
            # 生成key
            pics['key'] = key
            # 生成sha
            pics['sha'] = sha
            # 生成ss ——实体
            pics['ss'] = '组图'
            # es ——栏目名称
            pics['es'] = '期刊论文'
            # 生成ws ——目标网站
            pics['ws'] = 'sciencedirect'
            # 生成clazz ——层级关系
            pics['clazz'] = '组图_实体'
            # 生成biz ——项目
            pics['biz'] = '文献大数据_论文'
            # 生成ref
            pics['ref'] = ''
            # 采集责任人
            pics['creator'] = '张明星'
            # 更新责任人
            pics['modified_by'] = ''
            # 采集服务器集群
            pics['cluster'] = 'crawler'
            # 元数据版本号
            pics['metadata_version'] = 'V1.3'
            # 采集脚本版本号
            pics['script_version'] = 'V1.3'
            # 组图实体存入列表
            data_list.append(pics)

            # 存储图片种子
            for img in pic_datas:
                img_dict = {}
                img_dict['url'] = img['url']
                img_dict['title'] = img['title']
                img_dict['rel_esse'] = self.server.rela_entity(url, key, sha, '论文')
                img_dict['rel_pics'] = self.server.rela_entity(url, key, sha, '组图')

                suc = self.img_download(img_dict)
                if not suc:
                    return

        # 获取关联文档
        pdf_url = task_data.get('pdfUrl')
        if not pdf_url:
            paper_entity['rela_document'] = {}
            paper_entity['has_fulltext'] = 'None'
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

            # 存储文档实体全文
            suc = self.document(pdf_dict=pdf_dict, data_list=data_list)
            if not suc:
                paper_entity['has_fulltext'] = 'None'
                return
            else:
                paper_entity['has_fulltext'] = 'PDF'

        # 判断是否为真正论文
        if paper_entity['title'] and paper_entity['author'] and paper_entity['keyword'] and paper_entity['abstract'] and paper_entity.get('classification_code', ''):
            paper_entity['quality_score'] = '100'
        elif paper_entity['title'] and paper_entity['author'] and paper_entity['keyword']  and paper_entity.get('classification_code', ''):
            paper_entity['quality_score'] = '80'
        elif paper_entity['title'] and paper_entity['author'] and paper_entity['start_page'] and (paper_entity['references'] or paper_entity['cited_literature']):
            paper_entity['quality_score'] = '60'
        elif paper_entity['title'] and paper_entity['author'] and paper_entity['keyword'] and paper_entity['abstract']:
            paper_entity['quality_score'] = '40'
        elif paper_entity['title'] and paper_entity['author'] and paper_entity['keyword']:
            paper_entity['quality_score'] = '20'
        else:
            paper_entity['quality_score'] = '0'
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
            task = self.dao.get_one_task_from_redis(key=config.REDIS_SCIENCEDIRECT_PAPER)
            # task = '{"url": "https://www.sciencedirect.com/science/article/abs/pii/S0145212614001817", "pdfUrl": "", "type": "Editorial", "rights": "No access", "journalColumn": "Editorials", "journalUrl": "https://www.sciencedirect.com/journal/leukemia-research", "journalId": "leukemia-research", "year": "2014", "vol": "38", "issue": "9", "sha": "0000e4c66af9dbf3a26448b32f3d2a3b2593d22d"}'
            if not task:
                logger.info('task | 队列中已无任务')
                time.sleep(1)

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
