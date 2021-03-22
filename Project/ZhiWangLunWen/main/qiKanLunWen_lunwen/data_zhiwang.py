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
import requests
import traceback
import copy
import hashlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
from Log import logging
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config
from Utils import timeutils, timers
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY, LANG_API

LOG_FILE_DIR = 'ZhiWangLunWen'  # LOG日志存放路径
LOG_NAME = '期刊论文_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.LunWen_Data(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.lang_api = LANG_API
        self.timer = timers.Timer()
        self.s = requests.Session()

    def _get_resp(self, url, method, s=None, data=None, host=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download.get_resp(s=s, url=url, method=method, data=data, host=host,
                                          cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    logger.error('captcha | 出现验证码: {}'.format(url))
                    continue
            return resp
        else:
            return

    def img_download(self, img_dict):
        # 获取图片响应
        media_resp = self._get_resp(url=img_dict['url'], method='GET')
        if not media_resp:
            logger.error('downloader | 图片响应失败, url: {}'.format(img_dict['url']))
            # 标题内容调整格式
            img_dict['bizTitle'] = img_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储图片种子
            self.dao.save_task_to_mysql(table=config.MYSQL_IMG, memo=img_dict, ws='中国知网', es='论文')
            return
        # media_resp.encoding = media_resp.apparent_encoding
        img_content = media_resp.content
        # 存储图片
        content_type = 'image/jpeg'
        succ = self.dao.save_media_to_hbase(media_url=img_dict['url'], content=img_content, item=img_dict,
                                            type='image', contype=content_type)
        if not succ:
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            # 标题内容调整格式
            img_dict['bizTitle'] = img_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储图片种子
            self.dao.save_task_to_mysql(table=config.MYSQL_IMG, memo=img_dict, ws='中国知网', es='论文')
            return

    def handle(self, task_data, save_data):
        print(task_data)
        url = task_data['url']
        _id= self.server.get_id(url)
        # print(id)
        key = '中国知网|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()

        # 获取论文详情页html源码
        resp = self._get_resp(url=url, method='GET', s=self.s, host='kns.cnki.net')
        if not resp:
            logger.error('downloader | 论文详情页响应失败, url: {}'.format(url))
            return

        # resp.encoding = resp.apparent_encoding
        article_html = resp.text

        # ======================== 期刊论文实体数据 ===========================
        # 获取标题
        save_data['title'] = self.server.get_title(article_html)
        if not save_data['title']:
            return
        # 获取作者
        save_data['author'] = self.server.get_author(article_html)
        # 获取作者单位
        save_data['author_affiliation'] = self.server.get_affiliation(article_html)
        # 获取目录
        save_data['catalog'] = self.server.get_catalog(article_html)
        # 获取摘要
        save_data['abstract'] = []
        abstract = self.server.get_abstract(article_html)
        if abstract:
            ab_dict = {}
            ab_dict['text'] = abstract
            form_data = {'q': abstract}
            try:
                lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5, 10))
                lang = lang_resp.json().get('responseData').get('language')
            except:
                return
            ab_dict['lang'] = lang
            save_data['abstract'].append(ab_dict)
        # 获取关键词
        save_data['keyword'] = []
        keywords = self.server.get_keyword(article_html)
        if keywords:
            kw_dict = {}
            kw_dict['text'] = keywords
            form_data = {'q': keywords}
            try:
                lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5, 10))
                lang = lang_resp.json().get('responseData').get('language')
            except:
                return
            kw_dict['lang'] = lang
            save_data['keyword'].append(kw_dict)
        # 获取语种
        form_data = {'q': save_data['title']}
        try:
            lang_resp = requests.post(url=self.lang_api, data=form_data, timeout=(5, 10))
            lang = lang_resp.json().get('responseData').get('language')
        except:
            return
        save_data['language'] = lang
        # 获取基金
        save_data['funders'] = self.server.get_funders(article_html)
        # 数字对象标识符
        save_data['doi'] = self.server.get_more_fields(article_html, 'DOI')
        # 获取中图分类号
        save_data['classification_code'] = self.server.get_more_fields(article_html, '分类号')
        # 期刊名称
        save_data['journal_name'] = self.server.get_journal_name(article_html)
        year, vol, issue = self.server.get_year(article_html)
        # 年
        save_data['year'] = year
        # 卷号
        save_data['volume'] = vol
        # 期号
        save_data['issue'] = issue
        # 获取下载
        save_data['xiaZai'] = task_data.get('xiaZai', '')
        # 获取在线阅读
        save_data['zaiXianYueDu'] = task_data.get('zaiXianYueDu', '')
        # 获取下载次数
        save_data['downloads'] = self.server.get_info(article_html, '下载')
        # 获取所在页码
        save_data['start_page'] = re.findall(r"(\d+)-", self.server.get_info(article_html, '页码'))[0]
        save_data['end_page'] = re.findall(r"-(\d+)", self.server.get_info(article_html, '页码'))[0]
        # 获取页数
        save_data['total_page'] = self.server.get_info(article_html, '页数')
        # 获取大小
        save_data['size'] = self.server.get_info(article_html, '大小')
        # 学科类别
        save_data['subject_classification_name'] = task_data.get('xueKeLeiBie', '')
        # 获取参考文献
        save_data['references'] = self.server.canKaoWenXian(url=url, download=self._get_resp, s=self.s)
        # 获取引证文献
        save_data['cited_literature'] = self.server.canKaoWenXian(url=url, download=self._get_resp)
        # 获取文献数量年度分布
        save_data['annual_trend_of_literature_number'] = self.server.canKaoWenXian(url=url, download=self._get_resp)
        # 关联期刊
        save_data['rela_journal'] = self.server.rela_journal(task_data.get('parentUrl'))
        # 关联人物
        save_data['rela_creators'] = self.server.rela_creators(article_html)
        # 关联企业机构
        save_data['rela_organization'] = self.server.rela_organization(article_html)
        # 关联文档
        save_data['rela_document'] = {}

        # 获取所有图片链接
        pic_datas = self.server.get_pic_url(text=article_html, fetch=self._get_resp)
        if pic_datas:
            # 关联组图
            save_data['rela_pics'] = self.server.rela_pics(url, key, sha)
            # 组图实体
            pics = {}
            # 标题
            pics['title'] = save_data['title']
            # 组图内容
            pics['label_obj'] = self.server.get_pics(pic_datas)
            # 关联论文
            pics['rela_paper'] = self.server.rela_paper(url, key, sha)
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
            pics['ws'] = '中国知网'
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
            pics['metadata_version'] = 'V2.0'
            # 采集脚本版本号
            pics['script_version'] = 'V1.0'

            # 保存组图实体到Hbase
            pics_suc = self.dao.save_data_to_hbase(data=pics)
            if not pics_suc:
                logger.error('storage | 组图数据存储失败, url: {}'.format(url))
                return

            # 存储图片种子
            for img in pic_datas:
                img_dict = {}
                img_dict['url'] = img['url']
                img_dict['bizTitle'] = img['title']
                img_dict['relEsse'] = self.server.rela_paper(url, sha)
                img_dict['relPics'] = self.server.rela_pics(url, sha)
                # img_tasks.append(img_dict)

                # 存储图片种子
                suc = self.dao.save_task_to_mysql(table=config.MYSQL_IMG, memo=img_dict, ws='中国知网', es='论文')
                if not suc:
                    logger.error('seed | 图片种子存储失败, url: {}'.format(img['url']))

        else:
            # 关联组图
            save_data['relationPics'] = {}

        # ====================================公共字段
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
        save_data['ws'] = '中国知网'
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
        save_data['metadata_version'] = 'V1.2'
        # 采集脚本版本号
        save_data['script_version'] = 'V1.3'

        # =============== 存储部分 ==================
        # 保存人物队列
        people_list = self.server.getPeople(zuozhe=save_data['guanLianRenWu'], daoshi=save_data.get('guanLianDaoShi'), t=save_data['shiJian'])
        # print(people_list)
        if people_list:
            for people in people_list:
                author_suc = self.dao.save_task_to_mysql(table=config.MYSQL_PEOPLE, memo=people, ws='中国知网', es='论文')
                if not author_suc:
                    logger.error('seed | 人物种子存储失败, url: {}'.format(people['url']))

        # 保存机构队列
        if save_data['guanLianQiYeJiGou']:
            jigouList = copy.deepcopy(save_data['guanLianQiYeJiGou'])
            for jigou in jigouList:
                jigou_suc = self.dao.save_task_to_mysql(table=config.MYSQL_INSTITUTE, memo=jigou, ws='中国知网', es='论文')
                if not jigou_suc:
                    logger.error('seed | 机构种子存储失败, url: {}'.format(jigou['url']))

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
            # task = self.dao.get_one_task_from_redis(key=config.REDIS_QIKAN_PAPER)
            task = '{"theme": "基础医学研究", "url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=JYKY202001010&dbname=CJFDLAST2020", "xiaZai": "https://navi.cnki.net/knavi/Common/RedirectPage?sfield=XZ&q=n8sbjTFvPSUrNDkHGGwa1ho8r3UKR0Eg1blqUAXs46uVtWbBkzCDkcKJ5VmGgPhX&tableName=CJFDLAST2017", "zaiXianYueDu": "https://navi.cnki.net/knavi/Common/RedirectPage?sfield=RD&dbCode=CJFD&filename=SYKQ201705008&tablename=CJFDLAST2017&filetype=XML;EPUB;", "xueKeLeiBie": "医药卫生科技_口腔科学", "parentUrl": "https://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=SYKQ", "year": "2017", "issue": "05", "sha": "047fe93efaba692553e3eab9ff38bd58bbb593e2"}'
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


def start():
    main = SpiderMain()
    try:
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