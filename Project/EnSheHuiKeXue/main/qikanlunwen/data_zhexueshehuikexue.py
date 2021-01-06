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
from multiprocessing.pool import Pool, ThreadPool
from PyPDF2 import PdfFileReader

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Project.EnSheHuiKeXue.middleware import download_middleware
from Project.EnSheHuiKeXue.service import service
from Project.EnSheHuiKeXue.dao import dao
from Project.EnSheHuiKeXue import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import user_pool, timers
from Project.EnSheHuiKeXue.service.service import CaptchaProcessor

LOG_FILE_DIR = 'EnSheHuiKeXue'  # LOG日志存放路径
LOG_NAME = '英文论文_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BastSpiderMain(object):
    def __init__(self):
        # 下载中间件
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_type=config.PROXY_TYPE,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT,
                                                       proxy_country=config.COUNTRY,
                                                       proxy_city=config.CITY)
        self.server = service.Server(logging=logger)
        # 存储
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.timer = timers.Timer()
        self.s = requests.Session()
        self.captcha_processor = CaptchaProcessor(self.server, self.download, self.s, logger)
        self.num = 0

    # 检测PDF文件正确性
    # @staticmethod
    def is_valid_pdf_bytes_io(self, content, url, parent_url):
        b_valid = True
        try:
            reader = PdfFileReader(BytesIO(content), strict=False)
            if reader.getNumPages() < 1:  # 进一步通过页数判断。
                b_valid = False
        except:
            logger.error(str(traceback.format_exc()))
            msg = '检测PDF文件出错, url: {}'.format(url)
            logger.error(msg)
            data_dict = {'url': parent_url}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
            b_valid = False

        return b_valid

    # 获取文档实体字段
    def document(self, pdf_dict):
        logger.debug('document | 开始获取内容')
        self.timer.start()
        pdf_url = pdf_dict['url']
        # 获取页面响应
        pdf_resp = self.captcha_processor.process_first_request(url=pdf_url, method='GET', s=self.s)

        # 处理验证码
        pdf_resp = self.captcha_processor.process(pdf_resp)
        if pdf_resp is None:
            return

        if 'text' in pdf_resp.headers.get('Content-Type') or 'html' in pdf_resp.headers.get('Content-Type'):
            # 更新种子错误信息
            msg = 'url: {} Status: {} Content-Type error: {}'.format(pdf_url, pdf_resp.status_code,
                                                                         pdf_resp.headers['Content-Type'])
            logger.warning('document | failed, {} | url: {}'.format(msg, pdf_url))
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
            return

        # 内存中读写
        bytes_container = BytesIO()
        # 断点续爬，重试3次
        for retry_count in range(3):
            # 判断内容获取是否完整
            if pdf_resp.raw.tell() >= int(pdf_resp.headers.get('Content-Length', 0)):
                # 获取二进制内容
                bytes_container.write(pdf_resp.content)
                logger.info('document | 获取内容完整 | use time: {} | length: {}'.format(self.timer.use_time(),
                                                                                 len(bytes_container.getvalue())))
                # pdf_content += pdf_resp.content
                break
            else:
                # 获取二进制内容
                bytes_container.write(pdf_resp.content)
                logger.warning(
                    'document | 获取内容不完整 | use time: {} | length: {}'.format(self.timer.use_time(),
                                                                          len(bytes_container.getvalue())))
                # # 存储文档种子
                # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
                # 请求头增加参数
                ranges = 'bytes=%d-' % len(bytes_container.getvalue())
                # 断点续传
                pdf_resp = self.download.get_resp(url=pdf_url, method='GET', ranges=ranges, s=self.s)
                if not pdf_resp:
                    logger.error('document | 附件响应失败, url: {}'.format(pdf_url))
                    return
                continue
        else:
            # LOGGING.info('handle | 获取内容不完整 | use time: {} |
            # length: {}'.format('%.3f' % (time.time() - start_time),
            # len(bytes_container.getvalue())))
            # 更新种子错误信息
            msg = 'Content-Length error: {}/{}'.format(len(bytes_container.getvalue()),
                                                       pdf_resp.headers.get('Content-Length', 0))
            logger.warning('document | failed, {} | url: {}'.format(msg, pdf_url))
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='英文哲学社会科学', es='期刊论文', msg=msg)
            return

        # 获取二进制内容
        pdf_content = bytes_container.getvalue()
        logger.debug('document | 结束获取内容')

        # 检测PDF文件
        is_value = self.is_valid_pdf_bytes_io(pdf_content, pdf_url, pdf_dict['relEsse']['url'])
        if not is_value:
            # 更新种子错误信息
            msg = 'not PDF'
            logger.error('document | failed, {}, url: {}'.format(msg, pdf_url))
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
            return

        # 存储全文
        content_type = 'application/pdf'
        succ = self.dao.save_media_to_hbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict,
                                            type='document', contype=content_type)
        if not succ:
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            logger.error('document | failed save_media_to_hbase | url: {}'.format(pdf_url))
            return

        # 文档数据存储字典
        doc_data = dict()
        # 获取标题
        doc_data['title'] = pdf_dict['bizTitle']
        # 文档内容
        size = len(pdf_content)
        # size = len(pdf_content)
        doc_data['label_obj'] = self.server.getDocs(pdf_dict, size)
        # 获取来源网站
        doc_data['source_website'] = ""
        # 关联论文
        doc_data['rela_paper'] = pdf_dict['relEsse']

        self.server.clear()

        # ===================公共字段
        # url
        doc_data['url'] = pdf_dict['url']
        # 生成key
        doc_data['key'] = pdf_dict['key']
        # 生成sha
        doc_data['sha'] = hashlib.sha1(doc_data['key'].encode('utf-8')).hexdigest()
        # 生成ss ——实体
        doc_data['ss'] = '文档'
        # 生成es ——栏目名称
        doc_data['es'] = '英文期刊论文'
        # 生成ws ——目标网站
        doc_data['ws'] = '哲学社会科学外文OA资源数据库'
        # 生成clazz ——层级关系
        doc_data['clazz'] = '文档_论文文档'
        # 生成biz ——项目
        doc_data['biz'] = '文献大数据_英文论文'
        # 生成ref
        doc_data['ref'] = ''
        # 采集责任人
        doc_data['creator'] = '张明星'
        # 更新责任人
        doc_data['modified_by'] = ''
        # 采集服务器集群
        doc_data['cluster'] = 'crawler'
        # 元数据版本号
        doc_data['metadata_version'] = 'V1.1'
        # 采集脚本版本号
        doc_data['script_version'] = 'V1.3'

        # 保存数据到Hbase
        sto = self.dao.save_data_to_hbase(data=doc_data, ss_type=doc_data['ss'], sha=doc_data['sha'], url=doc_data['url'])

        if sto:
            logger.info('document | success, url: {}'.format(pdf_url))
            return True
        else:
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家社会哲学科学', es='期刊论文')
            logger.error('document | failed, url: {}'.format(pdf_url))
            return False

    def handle(self, task_data, save_data):
        print(task_data)
        url = task_data.get('url')
        _id = re.findall(r"id=(\w+)$", url)[0]
        # print(id)
        key = '哲学社会科学外文OA资源数据库|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()

        # 获取详情页
        profile_resp = self.captcha_processor.process_first_request(url=url, method='GET', s=self.s)

        # 处理验证码
        profile_resp = self.captcha_processor.process(profile_resp)
        if profile_resp is None:
            return

        profile_text = profile_resp.text
        # with open('profile.html', 'w') as f:
        #     f.write(profile_text)

        #
        # ========================== 获取实体 ============================
        # journal_information {'name': '', 'year': '', 'volume': '', 'issue': '', 'start_page': '', 'end_page': '', 'total_page': ''}
        # language
        # publisher
        # abstract [{'text': '', 'lang': ''}, {'text': '', 'lang': ''}]
        # keyword {'lang': '', 'text': ''}
        # author_affiliation
        # rela_journal
        # rela_document

        # 获取标题
        save_data['title'] = self.server.get_paper_title(profile_text)
        # 获取作者
        save_data['author'] = self.server.get_more_value(profile_text, '作者')
        # ISSN
        save_data['issn'] = {}
        print_issn = self.server.get_normal_value(profile_text, '印刷版ISSN')
        electronic_issn = self.server.get_normal_value(profile_text, '电子版ISSN')
        if print_issn:
            save_data['issn']['print'] = print_issn
        if electronic_issn:
            save_data['issn']['electronic'] = electronic_issn
        # DOI
        save_data['doi'] = {}
        doi = self.server.get_normal_value(profile_text, 'DOI')
        doi_url = self.server.get_full_link(profile_text, '全文链接')
        if doi:
            save_data['doi']['doi'] = doi
            save_data['doi']['doi_url'] = doi_url
        else:
            # 全文链接
            save_data['source_url'] = doi_url

        # 获取期刊信息
        save_data['journal_information'] = {}
        save_data['journal_information']['name'] = self.server.get_normal_value(profile_text, '期刊名称')
        save_data['journal_information']['year'] = self.server.get_normal_value(profile_text, '出版年度')
        save_data['journal_information']['volume'] = self.server.get_normal_value(profile_text, '卷号')
        save_data['journal_information']['issue'] = self.server.get_normal_value(profile_text, '期号')
        pages = self.server.get_normal_value(profile_text, '页码')
        if '-' in pages:
            save_data['journal_information']['start_page'] = re.findall(r"(.*)-", pages)[0]
            save_data['journal_information']['end_page'] = re.findall(r"-(.*)", pages)[0]
        else:
            save_data['journal_information']['total_page'] = pages

        # 获取摘要
        save_data['abstract'] = {}
        save_data['abstract']['text'] = self.server.getPaperAbstract(profile_text)
        if save_data['abstract']['text']:
            hasChinese = self.server.hasChinese(save_data['abstract']['text'])
            if hasChinese:
                save_data['abstract']['lang'] = "zh"
            else:
                save_data['abstract']['lang'] = "en"
        else:
            save_data['abstract']['lang'] = ""

        # 获取作者单位
        save_data['author_affiliation'] = self.server.getAuthorAffiliation(profile_text)

        # 获取关键词
        save_data['keyword'] = {}
        save_data['keyword']['text'] = self.server.getFieldValues(profile_text, '关 键 词')
        if save_data['keyword']['text']:
            if self.server.hasChinese(save_data['keyword']['text']):
                save_data['keyword']['lang'] = "zh"
            else:
                save_data['keyword']['lang'] = "en"
        else:
            save_data['keyword']['lang'] = ""
        # 获取项目基金
        save_data['funders'] = self.server.getFunders(profile_text)
        # 分类号
        save_data['classification_code'] = {}
        save_data['classification_code']['code'] = self.server.getFieldValues(profile_text, '分 类 号')
        if save_data['classification_code']['code']:
            save_data['classification_code']['type'] = "中图分类号"
        else:
            save_data['classification_code']['type'] = ""
        # 下载次数
        save_data['downloads'] = self.server.getCount(profile_text, '下载次数')
        # 在线阅读
        save_data['online_reading'] = self.server.getCount(profile_text, '在线阅读')
        # 关联期刊
        qikan_url = task_data.get('qikanUrl')
        qikan_id = re.findall(r"cn/(\w+)/?", qikan_url)[0]
        qikan_key = 'nssd.org|' + qikan_id
        qikan_sha = hashlib.sha1(qikan_key.encode('utf-8')).hexdigest()
        save_data['rela_journal'] = self.server.rela_journal(qikan_url, qikan_key, qikan_sha)
        # 获取关联文档
        pdf_url = task_data.get('pdfUrl')
        if pdf_url:
            doc_key = key
            doc_sha = hashlib.sha1(doc_key.encode('utf-8')).hexdigest()
            doc_url = pdf_url
            save_data['rela_document'] = self.server.rela_document(doc_url, doc_key, doc_sha)

            pdf_dict = dict()
            pdf_dict['url'] = doc_url
            pdf_dict['key'] = doc_key
            pdf_dict['id'] = _id
            pdf_dict['bizTitle'] = save_data['title']
            pdf_dict['relEsse'] = self.server.rela_paper(url, key, sha)
            pdf_dict['relPics'] = save_data['rela_document']

            # 删除响应数据缓存
            self.server.clear()
            # 存储文档实体及文档本身
            suc = self.document(pdf_dict=pdf_dict)
            if not suc:
                return

        else:
            # 删除响应数据缓存
            self.server.clear()
            save_data['rela_document'] = {}

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = key
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # es ——栏目名称
        save_data['es'] = '英文期刊论文'
        # 生成ws ——目标网站
        save_data['ws'] = '哲学社会科学外文OA资源数据库'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_论文'
        # 生成ref
        save_data['ref'] = ''
        # 采集责任人
        save_data['creator'] = '张明星'
        # 更新责任人
        save_data['modified_by'] = ''
        # 采集服务器集群
        save_data['cluster'] = 'crawler'
        # 元数据版本号
        save_data['metadata_version'] = 'V1.1'
        # 采集脚本版本号
        save_data['script_version'] = 'V1.3'

    def run(self):
        logger.info('thread start')
        task_timer = timers.Timer()
        # 第一次请求的等待时间
        self.timer.start()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.info('thread | wait download delay time | use time: {}'.format(self.timer.use_time()))
        # 单线程无限循环
        while True:
            # 获取任务
            logger.info('task start')
            task_timer.start()
            # task_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER, count=1,
            #                              lockname=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER_LOCK)
            # task = self.dao.get_one_task_from_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER)
            task = '{"url": "http://103.247.176.188/View.aspx?id=181612373", "pdfUrl": "http://103.247.176.188/Direct.aspx?dwn=1&id=181612373", "journalUrl": "http://103.247.176.188/ViewJ.aspx?id=138560", "sha": "0becc1c68892a344f00e262771d533c847c0dfd3"}'
            if task:
                try:
                    # 创建数据存储字典
                    save_data = dict()
                    # json数据类型转换
                    task_data = json.loads(task)
                    sha = task_data['sha']
                    # 获取字段值存入字典并返回sha
                    self.handle(task_data=task_data, save_data=save_data)
                    # 保存数据到Hbase
                    if not save_data:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | No data.'.format(task_timer.use_time()))
                        continue
                    if 'sha' not in save_data:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | Data Incomplete.'.format(task_timer.use_time()))
                        continue
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=save_data, ss_type=save_data['ss'], sha=save_data['sha'], url=save_data['url'])

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
                    logger.error('task end | task failed | use time: {}'.format(task_timer.use_time()))
            else:
                logger.info('task | 队列中已无任务')
                logger.info(self.captcha_processor.recognize_code.show_report())
                time.sleep(1)

    def start(self):
        # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

        # # 创建gevent协程
        # g_list = []
        # for i in range(8):
        #     s = gevent.spawn(self.run)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        thread_pool = ThreadPool(processes=config.THREAD_NUM)
        for thread_index in range(config.THREAD_NUM):
            thread_pool.apply_async(func=self.run)

        thread_pool.close()
        thread_pool.join()


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task="{'id': '207d122a-3a68-41b1-8d8a-f20552f22054', 'xueKeLeiBie': '信息科学部', 'url': 'http://ir.nsfc.gov.cn/paperDetail/207d122a-3a68-41b1-8d8a-f20552f22054'}")
    except:
        logger.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    # process_start()
    # 创建多进程
    po = Pool(processes=config.PROCESS_NUM)
    for _count in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
