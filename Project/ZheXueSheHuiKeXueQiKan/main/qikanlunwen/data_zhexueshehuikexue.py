# -*- coding:utf-8 -*-

import os
import sys
import hashlib
import json
import random
import re
import time
import traceback

# import gevent
# from gevent import monkey
# monkey.patch_all()
# from contextlib import closing
from io import BytesIO
from multiprocessing.pool import Pool, ThreadPool
from PyPDF2 import PdfFileReader
from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Project.ZheXueSheHuiKeXueQiKan.middleware import download_middleware
from Project.ZheXueSheHuiKeXueQiKan.service import service
from Project.ZheXueSheHuiKeXueQiKan.dao import dao
from Project.ZheXueSheHuiKeXueQiKan import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import user_pool

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"

# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/SheHuiKeXue/期刊论文_data_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        # cookie池
        self.cookie_obj = user_pool.CookieUtils(logging=logger)
        # 下载中间件
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY,
                                                                  cookie_obj=self.cookie_obj)
        # self.server = service.Server(logging=LOGGING)
        # 存储
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.num = 0

    def __get_resp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None, user=None):
        """

        :type referer: basestring
        """
        # 发现验证码，请求页面3次
        for _i in range(3):
            resp = self.download_middleware.getResp(url, method, s=s, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges, user=user)
            # if resp and resp.headers['Content-Type'].startswith('text'):
            #     if '请输入验证码' in resp.text:
            #         print('请重新登录')
            #         LOGGING.error('出现验证码: {}'.format(url))
            #         continue
            return resp
        else:
            return

    # 检测PDF文件正确性
    @staticmethod
    def is_valid_pdf_bytes_io(content):
        b_valid = True
        try:
            reader = PdfFileReader(BytesIO(content))
            if reader.getNumPages() < 1:  # 进一步通过页数判断。
                b_valid = False
        except:
            b_valid = False

        return b_valid

    # 获取文档实体字段
    def document(self, pdf_dict):
        # 新版本 1.1.0 并下载详情时，使用新URL进行采集
        new_url = pdf_dict['url']
        if hasattr(config, 'VERSION') and getattr(config, 'VERSION') == '1.1.0' and new_url.startswith(
                'http://www.nssd.org/articles/article_down.aspx?'):
            cookie_info = None
            new_url = 'http://www.nssd.org/articles/article_down.aspx?suid=5db370c4ebe73bb71f23fc9f8bdd68e7&id=' + pdf_dict.get('id')
            pdf_resp = self.__get_resp(url=new_url, method='GET')
        else:
            # 其它版本或非下载URL保持不变
            # 获取cookie
            cookie_info = self.cookie_obj.get_cookie()
            cookies = cookie_info['cookie']
            user = cookie_info['name']
            # 获取页面响应
            pdf_resp = self.__get_resp(url=new_url, method='GET', cookies=cookies, user=user)
        # self.num += 1
        # print('请求第 {} 篇全文'.format(self.num))
        logger.info('开始获取内容')
        start_time = time.time()
        if not pdf_resp:
            logger.error('附件响应失败, url: {}'.format(new_url))
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            return
        # media_resp.encoding = media_resp.apparent_encoding
        # 判断
        # print(pdf_resp['data'].headers['Content-Type'])
        if 'text' in pdf_resp['data'].headers['Content-Type'] or 'html' in pdf_resp['data'].headers['Content-Type']:
            if '请输入验证码' in pdf_resp['data'].text:
                logger.warning('请重新登录: {}'.format(new_url))
                # cookie使用次数+50
                if cookie_info is not None:
                    self.cookie_obj.max_cookie(cookie_info['name'])
                # 更新种子错误信息
                msg = '请重新登录'
                data_dict = {'url': pdf_dict['relEsse']['url']}
                self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
                return
            elif '今日下载数已满' in pdf_resp['data'].text:
                logger.warning('用户今日下载数已满，暂不提供全文下载! {}'.format(new_url))
                # cookie使用次数+50
                if cookie_info is not None:
                    self.cookie_obj.max_cookie(cookie_info['name'])
                # 更新种子错误信息
                msg = '当前用户今日下载数已满'
                data_dict = {'url': pdf_dict['relEsse']['url']}
                self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
                return
            elif '下载过于频繁' in pdf_resp['data'].text:
                logger.warning('当前IP下载过于频繁，暂不提供全文下载! {}, {}'.format(new_url, pdf_resp['proxy_ip']))
                # proxy权重减10
                self.download_middleware.proxy_obj.dec_max_proxy(pdf_resp['proxy_ip'])
                # 更新种子错误信息
                msg = '当前IP下载过于频繁'
                data_dict = {'url': pdf_dict['relEsse']['url']}
                self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
                return
            else:
                # 更新种子错误信息
                msg = 'url: {} StatusCode: {} Content-Type error: {}'.format(new_url, pdf_resp['data'].status_code,
                                                                             pdf_resp['data'].headers['Content-Type'])
                logger.warning(msg)
                logger.warning(pdf_resp['data'].text)
                data_dict = {'url': pdf_dict['relEsse']['url']}
                self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
                return

        # 内存中读写
        bytes_container = BytesIO()
        # 断点续爬，重试3次
        for retry_count in range(3):
            # 判断内容获取是否完整
            if pdf_resp['data'].raw.tell() >= int(pdf_resp['data'].headers.get('Content-Length', 0)):
                # 获取二进制内容
                bytes_container.write(pdf_resp['data'].content)
                logger.info('handle | 获取内容完整 | use time: {} | length: {}'.format('%.3f' % (time.time() - start_time),
                                                                                 len(bytes_container.getvalue())))
                # pdf_content += pdf_resp.content
                break
            else:
                # 获取二进制内容
                bytes_container.write(pdf_resp['data'].content)
                logger.warning('handle | 获取内容不完整 | use time: {} | length: {}'.format('%.3f' % (time.time() - start_time),
                                                                                 len(bytes_container.getvalue())))
                # # 存储文档种子
                # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
                # 请求头增加参数
                ranges = 'bytes=%d-' % len(bytes_container.getvalue())
                # 断点续传
                # pdf_resp = self.__get_resp(url=new_url, method='GET', ranges=ranges)
                # 分两种情况
                if hasattr(config, 'VERSION') and getattr(config, 'VERSION') == '1.1.0' and 'suid=' in new_url:
                    pdf_resp = self.__get_resp(url=new_url, method='GET', ranges=ranges)
                else:
                    # 其它版本或非下载URL保持不变
                    # 获取cookie
                    cookie_info = self.cookie_obj.get_cookie()
                    cookies = cookie_info['cookie']
                    user = cookie_info['name']
                    # 获取页面响应
                    pdf_resp = self.__get_resp(url=new_url, method='GET', cookies=cookies, user=user, ranges=ranges)
                if not pdf_resp:
                    logger.error('附件响应失败, url: {}'.format(new_url))
                    return
                continue
        else:
            # LOGGING.info('handle | 获取内容不完整 | use time: {} |
            # length: {}'.format('%.3f' % (time.time() - start_time),
            # len(bytes_container.getvalue())))
            # 更新种子错误信息
            msg = 'Content-Length error: {}/{}'.format(len(bytes_container.getvalue()),
                                                       pdf_resp['data'].headers.get('Content-Length', 0))
            logger.warning(msg)
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
            return

        # # 内存中读写
        # bytes_container = BytesIO()
        # # time_begin = time.time()
        # for i in range(3):
        #     try:
        #         # 自动释放连接
        #         with closing(pdf_resp) as response:
        #             for chunk in response.iter_content(chunk_size=4096):
        #                 if chunk:
        #                     # time_end = time.time()
        #                     # if time_end - time_begin >= 2:
        #                     #     LOGGING.info("handle | RequestTooLong Timeout | use time: {} | length: {}".
        #                     # format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #                     #     # 存储文档种子
        #                     #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT,
        #                     #                              memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #                     #     return
        #
        #                     bytes_container.write(chunk)
        #                     # time_begin = time.time()
        #     except Exception as e:
        #         LOGGING.info("handle | 获取内容失败 | use time: {} | length: {} | message: {}".format(
        #             '%.3f' % (time.time() - start_time), len(bytes_container.getvalue()), e))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__get_resp(url=new_url, method='GET', ranges=ranges)
        #         continue
        #
        #     # 判断内容获取是否完整
        #     if pdf_resp.raw.tell() >= int(pdf_resp.headers['Content-Length']):
        #         LOGGING.info('handle | 获取内容完整 | use time: {} | length: {}'.format('%.3f' % (time.time() - start_time),
        #                                                                            len(bytes_container.getvalue())))
        #         break
        #     else:
        #         LOGGING.info('handle | 获取内容失败 | use time: {} | ' +
        #                      'length: {}'.format('%.3f' % (time.time() - start_time),
        #                                          len(bytes_container.getvalue())))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__get_resp(url=new_url, method='GET', ranges=ranges)
        # else:
        #     LOGGING.info('handle | 获取内容不完整 | use time: {} | length: {}'.
        #                  format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #     # 存储文档种子
        #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #     return
        #
        # 获取二进制内容
        pdf_content = bytes_container.getvalue()
        logger.info('结束获取内容')

        # 检测PDF文件
        is_value = self.is_valid_pdf_bytes_io(pdf_content)
        if not is_value:
            # 更新种子错误信息
            msg = 'not PDF'
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文', msg=msg)
            return

        # with open('profile.pdf', 'wb') as f:
        #     f.write(pdf_content)

        # 存储全文
        content_type = 'application/pdf'
        succ = self.dao.saveMediaToHbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict, type='document',
                                         contype=content_type)
        if not succ:
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

        server = service.Server(logging=logger)

        # 文档数据存储字典
        doc_data = dict()
        # 获取标题
        doc_data['title'] = pdf_dict['bizTitle']
        # 文档内容
        size = len(pdf_content)
        # size = len(pdf_content)
        doc_data['label_obj'] = server.getDocs(pdf_dict, size)
        # 获取来源网站
        doc_data['source_website'] = ""
        # 关联论文
        doc_data['rela_paper'] = pdf_dict['relEsse']

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
        doc_data['es'] = '论文'
        # 生成ws ——目标网站
        doc_data['ws'] = '国家哲学社会科学学术期刊数据库'
        # 生成clazz ——层级关系
        doc_data['clazz'] = '文档_论文文档'
        # 生成biz ——项目
        doc_data['biz'] = '文献大数据_论文'
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

        logger.info('文档数据开始存储')
        # 保存数据到Hbase
        sto = self.dao.saveDataToHbase(data=doc_data)

        if sto:
            logger.info('文档数据存储成功, sha: {}'.format(doc_data['sha']))
            return True
        else:
            logger.error('文档数据存储失败, url: {}'.format(doc_data['url']))
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家社会哲学科学', es='期刊论文')
            return

    def handle(self, task_data, save_data):
        # print(task_data)
        url = task_data.get('url')
        _id = re.findall(r"id=(.*)?&?", url)[0]
        # print(id)
        key = 'nssd.org|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()
        # xueKeLeiBie = task_data.get('xuekeleibie')

        server = service.Server(logging=logger)

        # # 获取详情页
        # profile_resp = self.__getResp(url=url, method='GET')
        # if not profile_resp:
        #     LOGGING.error('详情页响应失败, url: {}'.format(url))
        #     return
        #
        # profile_text = profile_resp.text
        #
        # # ========================== 获取实体 ============================
        # server = service.Server(logging=LOGGING)
        # # 获取标题
        # save_data['title'] = server.getPaperTitle(profile_text)
        # # 存入mysql数据库
        # data_dict = {'url': url, 'title': save_data['title']}
        # self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家哲学社会科学', es='期刊论文')
        # # 获取摘要
        # save_data['abstract'] = {}
        # save_data['abstract']['text'] = server.getPaperAbstract(profile_text)
        # if save_data['abstract']['text']:
        #     hasChinese = server.hasChinese(save_data['abstract']['text'])
        #     if hasChinese:
        #         save_data['abstract']['lang'] = "zh"
        #     else:
        #         save_data['abstract']['lang'] = "en"
        # else:
        #     save_data['abstract']['lang'] = ""
        # # 获取作者
        # save_data['author'] = task_data.get('authors')
        # # 获取作者单位
        # save_data['author_affiliation'] = server.getAuthorAffiliation(profile_text)
        # # 获取作者单位
        # save_data['journal_information'] = {}
        # save_data['journal_information']['name'] = server.getJournalName(profile_text)
        # save_data['journal_information']['year'] = task_data.get('year')
        # save_data['journal_information']['issue'] = task_data.get('issue')
        # save_data['journal_information']['start_page'] = server.getStartPage(profile_text)
        # save_data['journal_information']['end_page'] = server.getEndPage(profile_text)
        # save_data['journal_information']['total_page'] = server.getTotalPages(profile_text)
        # # 获取关键词
        # save_data['keyword'] = {}
        # save_data['keyword']['text'] = server.getFieldValues(profile_text, '关 键 词')
        # if save_data['keyword']['text']:
        #     if server.hasChinese(save_data['keyword']['text']):
        #         save_data['keyword']['lang'] = "zh"
        #     else:
        #         save_data['keyword']['lang'] = "en"
        # else:
        #     save_data['keyword']['lang'] = ""
        # # 获取项目基金
        # save_data['funders'] = server.getFunders(profile_text)
        # # 分类号
        # save_data['classification_code'] = {}
        # save_data['classification_code']['code'] = server.getFieldValues(profile_text, '分 类 号')
        # if save_data['classification_code']['code']:
        #     save_data['classification_code']['type'] = "中图分类号"
        # else:
        #     save_data['classification_code']['type'] = ""
        # # 下载次数
        # save_data['downloads'] = server.getCount(profile_text, '下载次数')
        # # 在线阅读
        # save_data['online_reading'] = server.getCount(profile_text, '在线阅读')
        # # 学科分类
        # save_data['subject_classification_name'] = xueKeLeiBie
        # # 关联期刊
        # qikan_url = task_data.get('qikanUrl')
        # qikan_id = re.findall(r"cn/(\w+)/?", qikan_url)[0]
        # qikan_key = 'nssd.org|' + qikan_id
        # qikan_sha = hashlib.sha1(qikan_key.encode('utf-8')).hexdigest()
        # save_data['rela_journal'] = server.rela_journal(qikan_url, qikan_key, qikan_sha)
        # 获取关联文档
        pdf_url = task_data.get('pdfUrl')
        if pdf_url:
            doc_key = key
            doc_sha = hashlib.sha1(doc_key.encode('utf-8')).hexdigest()
            doc_url = pdf_url
            save_data['rela_document'] = server.rela_document(doc_url, doc_key, doc_sha)

            pdf_dict = dict()
            pdf_dict['url'] = doc_url
            pdf_dict['key'] = doc_key
            pdf_dict['id'] = task_data.get('id')
            pdf_dict['bizTitle'] = task_data.get('title')
            pdf_dict['relEsse'] = server.rela_paper(url, key, sha)
            pdf_dict['relPics'] = save_data['rela_document']

            # 删除响应数据缓存
            server.get_new_text()
            # 存储文档实体及文档本身
            suc = self.document(pdf_dict=pdf_dict)
            if not suc:
                return

        else:
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
        save_data['es'] = '期刊论文'
        # 生成ws ——目标网站
        save_data['ws'] = '国家哲学社会科学学术期刊数据库'
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
        logger.info('线程启动')
        # 第一次请求的等待时间
        delay_time = time.time()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.info('handle | download delay | use time: {}'.format('%.3f' % (time.time() - delay_time)))
        # 单线程无限循环
        while True:
            # 获取任务
            start_time = time.time()
            # task_list = self.dao.getTask(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER, count=1,
            #                              lockname=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER_LOCK)
            # task_list = ['{"url": "http://www.nssd.org/articles/article_detail.aspx?
            # id=12165488", "authors": "鲁歌|刘娜",
            #    "pdfUrl": "http://www.nssd.org/articles/article_down.aspx?id=12165488",
            #    "id": "12165488", "qikanUrl": "http://www.nssd.org/journal/cn/96698B/",
            #    "xuekeleibie": "文化科学", "year": "1992", "issue": "03",
            #    "sha": "0007c10a1b210642cfa783c6cf67d076570535aa",
            #    "title": "《金瓶梅》作者是贾梦龙吗？"}']
            task = self.dao.get_one_task(key=config.REDIS_ZHEXUESHEHUIKEXUE_PAPER)
            if task:
                try:
                    # 创建数据存储字典
                    save_data = {}
                    # json数据类型转换
                    task_data = json.loads(task)
                    sha = task_data['sha']
                    # 获取字段值存入字典并返回sha
                    self.handle(task_data=task_data, save_data=save_data)
                    # 保存数据到Hbase
                    if not save_data:
                        logger.info('没有获取数据, 存储失败')
                        # 逻辑删除任务
                        self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                        logger.info(
                            'handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))
                        continue
                    if 'sha' not in save_data:
                        logger.info('数据获取不完整, 存储失败')
                        # 逻辑删除任务
                        self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                        logger.info(
                            'handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))
                        continue
                    logger.info('论文数据开始存储')
                    # 存储数据
                    success = self.dao.saveDataToHbase(data=save_data)

                    if success:
                        logger.info('论文数据存储成功')
                        # 已完成任务
                        self.dao.finishTask(table=config.MYSQL_PAPER, sha=sha)
                        # # 删除任务
                        # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                    else:
                        logger.info('论文数据存储失败')
                        # 逻辑删除任务
                        self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)

                    logger.info('handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))

                except:
                    logger.exception(str(traceback.format_exc()))
                    logger.info('handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))
            else:
                time.sleep(1)
                logger.info('handle | task complete | use time: {}'.format('%.3f' % (time.time() - start_time)))

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
    logger.info('======The Start!======')
    begin_time = time.time()
    # process_start()
    # 创建多进程
    po = Pool(processes=config.PROCESS_NUM)
    for _count in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
