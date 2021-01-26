# -*- coding:utf-8 -*-

# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import hashlib
import json
import random
import re
import time
import traceback
from multiprocessing.pool import Pool, ThreadPool

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))

from Log import logging
from Project.EnSheHuiKeXue import config
from Project.EnSheHuiKeXue.dao import dao
from Project.EnSheHuiKeXue.middleware import download_middleware
from Project.EnSheHuiKeXue.service import service
from Utils import timeutils, timers
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY

LOG_FILE_DIR = 'EnSheHuiKeXue'  # LOG日志存放路径
LOG_NAME = '英文期刊_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class BaseSpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Downloader(logging=logger,
                                                       proxy_enabled=config.PROXY_ENABLED,
                                                       stream=config.STREAM,
                                                       timeout=config.TIMEOUT)
        self.server = service.Server(logging=logger)
        self.dao = dao.Dao(logging=logger,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BaseSpiderMain):
    def __init__(self):
        super().__init__()
        self.timer = timers.Timer()

    def handle(self, task_data, save_data):
        # print(task_data)
        url = task_data.get('url')
        _id = re.findall(r"id=(\w+)$", url)[0]
        # print(id)
        key = '哲学社会科学外文OA资源数据库|' + _id
        sha = hashlib.sha1(key.encode('utf-8')).hexdigest()

        # 获取期刊详情页
        profile_resp = self.download.get_resp(url=url, method='GET')
        if not profile_resp:
            logger.error('downloader | 详情页响应失败, url: {}'.format(url))
            return

        profile_text = profile_resp.text

        # ========================== 获取期刊实体 ============================
        # 获取标题
        save_data['title'] = self.server.get_journal_title(profile_text)
        # 获取简介
        save_data['abstract'] = []
        en_abstract_text = self.server.get_normal_value(profile_text, '期刊简介')
        if en_abstract_text:
            en_abstract = {}
            en_abstract['text'] = en_abstract_text
            en_abstract['lang'] = self.server.get_lang(en_abstract['text'])
            save_data['abstract'].append(en_abstract)
        zh_abstract_text = self.server.get_normal_value(profile_text, '中文简介')
        if zh_abstract_text:
            zh_abstract = {}
            zh_abstract['text'] = zh_abstract_text
            zh_abstract['lang'] = self.server.get_lang(zh_abstract['text'])
            save_data['abstract'].append(zh_abstract)
        # ISSN
        save_data['issn'] = self.server.get_normal_value(profile_text, 'ISSN(Print)')
        save_data['e_issn'] = self.server.get_normal_value(profile_text, 'ISSN(Electronic)')
        # 出版社
        save_data['publisher'] = self.server.get_multi_value(profile_text, '出版社')
        # 主编
        save_data['chief_editor'] = self.server.get_normal_value(profile_text, '主编')
        # 出版国
        save_data['country_of_publication'] = self.server.get_normal_value(profile_text, '出版国')
        # 语种
        save_data['language'] = self.server.get_multi_value(profile_text, '语种')
        # 出版频率
        save_data['period'] = self.server.get_normal_value(profile_text, '出版频率')
        # 创刊年
        save_data['start_year_of_publication'] = self.server.get_normal_value(profile_text, '创刊年')
        # 停刊年
        save_data['stop_year_of_publication'] = self.server.get_normal_value(profile_text, '停刊年')
        # 中图分类
        save_data['classification_code'] = self.server.get_classification_value(profile_text, '中图分类')
        # 期刊网址
        save_data['journal_website'] = self.server.get_journal_website(profile_text, '期刊网址')

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = key
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '期刊'
        # 生成es ——栏目名称
        save_data['es'] = '英文期刊'
        # 生成ws ——目标网站
        save_data['ws'] = '哲学社会科学外文OA资源数据库'
        # 生成clazz ——层级关系
        save_data['clazz'] = '期刊_学术期刊'
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
        task_timer = timers.Timer()
        logger.info('thread | start')
        # 第一次请求的等待时间
        self.timer.start()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        logger.info('thread | wait download delay time| use time: {}'.format(self.timer.use_time()))
        # 单线程无限循环
        while True:
            # 获取任务
            logger.info('task start')
            task_timer.start()
            task = self.dao.get_one_task_from_redis(key=config.REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE)
            # task = '{"url": "http://103.247.176.188/ViewJ.aspx?id=81767", "sha": "38feb69bbe48bf5d66f505310fa452d8eb184b65"}'
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
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | No data.'.format(task_timer.use_time()))
                        continue
                    if 'sha' not in save_data:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        logger.error(
                            'task end | task failed | use time: {} | Data Incomplete.'.format(task_timer.use_time()))
                        continue
                    # 存储数据
                    success = self.dao.save_data_to_hbase(data=save_data, ss_type=save_data['ss'], sha=save_data['sha'], url=save_data['url'])

                    if success:
                        # 已完成任务
                        self.dao.finish_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
                        # # 删除任务
                        # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                    else:
                        # 逻辑删除任务
                        self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)

                    logger.info(
                        'task end | task success | use time: {}'.format(task_timer.use_time()))

                except:
                    logger.exception(str(traceback.format_exc()))
                    logger.error('task end | task failed | use time: {}'.format(task_timer.use_time()))
            else:
                time.sleep(1)
                continue


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
    threadpool = ThreadPool(processes=config.THREAD_NUM)
    for j in range(config.THREAD_NUM):
        threadpool.apply_async(func=start)

    threadpool.close()
    threadpool.join()


if __name__ == '__main__':
    logger.info('====== The Start! ======')
    begin_time = time.time()
    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    logger.info('====== The End! ======')
    logger.info('====== Time consuming is %.3fs ======' % (end_time - begin_time))
