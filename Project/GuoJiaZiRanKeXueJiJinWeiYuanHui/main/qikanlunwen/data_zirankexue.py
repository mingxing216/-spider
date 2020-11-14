# -*- coding:utf-8 -*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import traceback
import hashlib
import random
import re
import requests
from datetime import datetime
from contextlib import closing
import json
import threading
from io import BytesIO, StringIO
from multiprocessing.pool import Pool, ThreadPool
from PyPDF2 import PdfFileReader
from loguru import logger

# sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../")))

from Utils import timeutils
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY

logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"
# 输出到指定目录下的log文件，并按天分隔
logger.add("/opt/Log/ZiRanKeXue/论文_data_{time}.log",
           format=logger_format,
           level="INFO",
           rotation='00:00',
           # compression='zip',
           enqueue=True,
           encoding="utf-8")


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=logger,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

        self.profile_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperInfo'

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges)
            if resp and resp['data'].headers.get('Content-Type').startswith('text'):
                if '请输入验证码' in resp['data'].text:
                    logger.error('出现验证码: {}'.format(url))
                    continue

            return resp

        else:
            return

    # 检测PDF文件正确性
    @staticmethod
    def is_valid_pdf_bytes_io(content):
        b_valid = True
        try:
            reader = PdfFileReader(BytesIO(content), strict=False)
            if reader.getNumPages() < 1:  # 进一步通过页数判断。
                b_valid = False
        except:
            logger.error(str(traceback.format_exc()))
            b_valid = False

        return b_valid

    # 获取文档实体字段
    def document(self, pdf_dict):
        # 获取页面响应
        pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET')
        if not pdf_resp['data']:
            msg = '附件响应失败, url: {} msg: {}'.format(pdf_dict['url'], pdf_resp['message'])
            logger.error(msg)
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家自然科学基金委员会', es='论文', msg=msg)
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

        if pdf_resp['status'] not in [200, 206]:
            msg = '附件响应状态码错误, status: {} url: {}'.format(pdf_resp['status'], pdf_dict['url'])
            logger.error(msg)
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家自然科学基金委员会', es='论文', msg=msg)
            return

        # media_resp.encoding = media_resp.apparent_encoding

        logger.info('开始获取内容')
        start_time = time.time()

        # 内存中读写
        bytes_container = BytesIO()
        # 断点续爬，重试3次
        for i in range(3):
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
                logger.info('handle | 获取内容不完整 | use time: {} | length: {}'.format('%.3f' % (time.time() - start_time),
                                                                                  len(bytes_container.getvalue())))
                # # 存储文档种子
                # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
                # 请求头增加参数
                ranges = 'bytes=%d-' % len(bytes_container.getvalue())
                # 断点续传
                pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET', ranges=ranges)
                if not pdf_resp['data']:
                    logger.error('附件响应失败, url: {}'.format(pdf_dict['url']))
                    return
                continue
        else:
            # 更新种子错误信息
            msg = 'Content-Length error: {}/{}'.format(len(bytes_container.getvalue()),
                                                       pdf_resp['data'].headers.get('Content-Length', 0))
            logger.warning(msg)
            data_dict = {'url': pdf_dict['relEsse']['url']}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家自然科学基金委员会', es='论文', msg=msg)
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
        #                     #     LOGGING.info("handle | RequestTooLong Timeout | use time: {}s | length: {}".format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #                     #     # 存储文档种子
        #                     #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #                     #     return
        #
        #                     bytes_container.write(chunk)
        #                     # time_begin = time.time()
        #     except Exception as e:
        #         LOGGING.info("handle | 获取内容失败 | use time: {}s | length: {} | message: {}".format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue()), e))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET', ranges=ranges)
        #         continue
        #
        #     # 判断内容获取是否完整
        #     if pdf_resp.raw.tell() >= int(pdf_resp.headers['Content-Length']):
        #         LOGGING.info('handle | 获取内容完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #         break
        #     else:
        #         LOGGING.info('handle | 获取内容失败 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET', ranges=ranges)
        # else:
        #     LOGGING.info('handle | 获取内容不完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #     # 存储文档种子
        #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #     return
        #
        # 获取二进制内容
        pdf_content = bytes_container.getvalue()
        # with open('profile.pdf', 'wb') as f:
        #     f.write(pdf_resp)
        logger.info('结束获取内容')

        # 检测PDF文件
        isValue = self.is_valid_pdf_bytes_io(pdf_content)
        if not isValue:
            return

        # 第一次存储文档
        con = 'ABC'.encode('utf-8')
        suc = self.dao.save_media_to_hbase(media_url=pdf_dict['url'], content=con, item=pdf_dict, type='document')
        if not suc:
            return

        # 存储真正文档
        content_type = 'application/pdf'
        succ = self.dao.save_media_to_hbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict,
                                            type='document', contype=content_type)
        if not succ:
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

        # 文档数据存储字典
        doc_data = {}
        # 获取标题
        doc_data['title'] = pdf_dict['bizTitle']
        # 文档内容
        size = len(pdf_content)
        doc_data['label_obj'] = self.server.getDocs(pdf_dict, size)
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
        doc_data['ws'] = '国家自然科学基金委员会'
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
        sto = self.dao.save_data_to_hbase(data=doc_data)

        if sto:
            logger.info('文档数据存储成功, sha: {}'.format(doc_data['sha']))
            return True
        else:
            logger.error('文档数据存储失败, url: {}'.format(doc_data['url']))
            # # 存储文档种子
            # self.dao.save_task_to_mysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

    def handle(self, task_data, save_data):
        # print(task_data)
        id = task_data.get('id')
        key = 'ir.nsfc.gov.cn|' + id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()
        url = task_data.get('url')
        xueKeLeiBie = task_data.get('fieldName')

        # POST请求参数
        payload = {'achievementID': id}

        # 获取详情页
        profile_resp = self.__getResp(url=self.profile_url, method='POST', data=json.dumps(payload))
        if not profile_resp['data']:
            msg = '详情页响应失败, url: {} msg: {}'.format(url, profile_resp['message'])
            logger.error(msg)
            data_dict = {'url': url}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家自然科学基金委员会', es='论文', msg=msg)
            return

        if profile_resp['status'] not in [200, 206]:
            msg = '详情页响应状态码错误, status: {} url: {}'.format(profile_resp['status'], url)
            logger.error(msg)
            data_dict = {'url': url}
            self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=data_dict, ws='国家自然科学基金委员会', es='论文', msg=msg)
            return

        # profile_resp.encoding = profile_resp.apparent_encoding
        try:
            profile_json = profile_resp['data'].json()
            # 获取浏览次数
            browseCount = profile_json['data'][0].get('browseCount')
            # 获取下载次数
            downloadCount = profile_json['data'][0].get('downloadCount')
        except Exception:
            return

        # ========================== 获取实体 ============================
        # 获取标题
        save_data['title'] = task_data.get('chineseTitle')
        # 获取作者
        save_data['author'] = self.server.getMoreFieldValue(task_data.get('authors'))
        # 获取成果类型
        productType = int(task_data.get('productType'))
        if productType == 3:
            # 成果类型
            save_data['type'] = '会议论文'
            # es ——栏目名称
            save_data['es'] = '会议论文'
            # 生成clazz ——层级关系
            save_data['clazz'] = '论文_会议论文'
            # 获取会议名称
            save_data['conference_name'] = task_data.get('journal')
            # 获取语种
            if task_data.get('journal'):
                hasChinese = self.server.hasChinese(task_data.get('journal'))
                if hasChinese:
                    save_data['language'] = "zh"
                else:
                    save_data['language'] = "en"
            else:
                save_data['language'] = ""
        elif productType == 4:
            # 成果类型
            save_data['type'] = '期刊论文'
            # es ——栏目名称
            save_data['es'] = '期刊论文'
            # 生成clazz ——层级关系
            save_data['clazz'] = '论文_期刊论文'
            # 获取期刊名称
            save_data['journal_name'] = task_data.get('journal')
            # 获取语种
            if task_data.get('journal'):
                hasChinese = self.server.hasChinese(task_data.get('journal'))
                if hasChinese:
                    save_data['language'] = "zh"
                else:
                    save_data['language'] = "en"
            else:
                save_data['language'] = ""
        # 获取数字对象标识符
        save_data['doi'] = {}
        save_data['doi']['doi'] = task_data.get('doi')
        save_data['doi']['doi_url'] = task_data.get('doiUrl')
        # 获取时间
        shiJian = task_data.get('publishDate')
        if shiJian:
            try:
                save_data['date'] = timeutils.getDateTimeRecord(shiJian)

            except:
                save_data['date'] = shiJian
        else:
            save_data['date'] = ""
        # 获取年
        year = task_data.get('publishDate')
        if year:
            save_data['year'] = re.findall(r"\d{4}", year)[0]
        else:
            save_data['year'] = ""
            # 获取关键词
        save_data['keyword'] = {}
        save_data['keyword']['text'] = self.server.getMoreFieldValue(task_data.get('zhKeyword'))
        if save_data['keyword']['text']:
            hasChinese = self.server.hasChinese(save_data['keyword']['text'])
            if hasChinese:
                save_data['keyword']['lang'] = "zh"
            else:
                save_data['keyword']['lang'] = "en"
        else:
            save_data['keyword']['lang'] = ""
        # 获取摘要
        save_data['abstract'] = {}
        save_data['abstract']['text'] = task_data.get('zhAbstract')
        if save_data['abstract']['text']:
            hasChinese = self.server.hasChinese(save_data['abstract']['text'])
            if hasChinese:
                save_data['abstract']['lang'] = "zh"
            else:
                save_data['abstract']['lang'] = "en"
        else:
            save_data['abstract']['lang'] = ""
        # 获取项目
        save_data['funders'] = {}
        # 获取项目类型
        save_data['funders']['project_type'] = task_data.get('supportTypeName')
        # 获取项目编号
        save_data['funders']['project_number'] = task_data.get('fundProjectNo')
        # 获取项目名称
        save_data['funders']['project_name'] = task_data.get('fundProject')
        # 项目代码
        save_data['funders']['project_code'] = task_data.get('fundProjectCode')
        # 获取研究机构
        save_data['orgnization_name'] = task_data.get('organization')
        # 获取点击量
        save_data['online_reading'] = browseCount
        # 获取下载次数
        save_data['downloads'] = downloadCount
        # 获取学科类别
        save_data['classification_code'] = {}
        save_data['classification_code']['name'] = self.server.getXueKeLeiBie(profile_json, 'fieldName', xueKeLeiBie)
        # 获取学科领域代码
        save_data['classification_code']['code'] = task_data.get('fieldCode')
        save_data['classification_code']['type'] = 'NSFC'

        # 获取关联文档
        doc_id = task_data.get('fulltext')
        if doc_id:
            doc_key = 'ir.nsfc.gov.cn|' + doc_id
            doc_sha = hashlib.sha1(doc_key.encode('utf-8')).hexdigest()
            doc_url = task_data.get('pdfUrl')
            save_data['rela_document'] = self.server.guanLianWenDang(doc_url, doc_key, doc_sha)

            pdf_dict = {}
            pdf_dict['url'] = doc_url
            pdf_dict['key'] = doc_key
            pdf_dict['bizTitle'] = save_data['title']
            pdf_dict['relEsse'] = self.server.guanLianLunWen(url, key, sha)
            pdf_dict['relPics'] = save_data['rela_document']

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
        # 生成ws ——目标网站
        save_data['ws'] = '国家自然科学基金委员会'
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
        logger.info('handle | download delay | use time: {}s'.format('%.3f' % (time.time() - delay_time)))
        # 单线程无限循环
        while True:
            # 获取任务
            start_time = time.time()
            # task_list = self.dao.get_task_from_redis(key=config.REDIS_ZIRANKEXUE_PAPER, count=1,
            #                                          lockname=config.REDIS_ZIRANKEXUE_PAPER_LOCK)
            # task_list = ['{"achievementID": "ZD193973", "authors": "", "chineseTitle": "Semi-Supervised Learning for Neural Machine Translation", "conference": "", "doi": "10.18653/v1/p16-1185", "doiUrl": "https://doi.org/10.18653/v1/p16-1185", "downloadHref": "", "enAbstract": "", "enKeyword": "", "englishTitle": "", "fieldCode": "F011305", "fulltext": "ZD193973", "fundProject": "跨语言社会舆情分析基础理论与关键技术研究", "fundProjectCode": "970061", "fundProjectNo": "61331013", "id": "aa16eaa8-a45c-4994-a42b-9cb80a8fc09d", "journal": "Annual Meeting of the Association for Computational Linguistics", "organization": "中央民族大学", "organizationID": "201617", "outputSubIrSource": "", "pageRange": "", "productType": "3", "publishDate": "2016-08-07", "source": "origin", "supportType": "220", "supportTypeName": "重点项目", "year": "2016-08-07", "zhAbstract": "While end-to-end neural machine translation (NMT) has made remarkable progress recently, NMT systems only rely on parallel corpora for parameter estimation. Since parallel corpora are usually limited in quantity, quality, and coverage, especially for low-resource languages, it is appealing to exploit monolingual corpora to improve NMT. We propose a semisupervised approach for training NMT models on the concatenation of labeled (parallel corpora) and unlabeled (monolingual corpora) data. The central idea is to reconstruct the monolingual corpora using an autoencoder, in which the sourceto-target and target-to-source translation models serve as the encoder and decoder, respectively. Our approach can not only exploit the monolingual corpora of the target language, but also of the source language. Experiments on the Chinese English dataset show that our approach achieves significant improvements over state-of-the-art SMT and NMT systems.", "zhKeyword": "", "fieldName": "信息科学部", "url": "http://ir.nsfc.gov.cn/paperDetail/aa16eaa8-a45c-4994-a42b-9cb80a8fc09d", "pdfUrl": "http://ir.nsfc.gov.cn/paperDownload/ZD193973.pdf", "sha": "00052f292efbd1d1a25728aca9d79f288fc15d86"}']
            task = self.dao.get_one_task_from_redis(key=config.REDIS_ZIRANKEXUE_PAPER_RETRY)
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
                        logger.info('没有获取数据, 存储失败')
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.info(
                            'handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))
                        continue
                    if 'sha' not in save_data:
                        logger.info('数据获取不完整, 存储失败')
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        logger.info(
                            'handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))
                        continue
                    logger.info('论文数据开始存储')
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=save_data)

                    if success:
                        logger.info('论文数据存储成功')
                        # 已完成任务
                        self.dao.finish_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)
                        # # 删除任务
                        # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                    else:
                        logger.info('论文数据存储失败')
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PAPER, sha=sha)

                    logger.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))

                except:
                    logger.exception(str(traceback.format_exc()))
                    logger.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))
            else:
                logger.info('队列中已无任务')
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
        threadpool = ThreadPool(processes=config.THREAD_NUM)
        for i in range(config.THREAD_NUM):
            threadpool.apply_async(func=self.run)

        threadpool.close()
        threadpool.join()


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

    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('======The End!======')
    logger.info('====== Time consuming is %.2fs ======' % (end_time - begin_time))
