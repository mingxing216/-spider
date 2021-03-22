# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import copy
import time
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_作者_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.ZhiWangLunWen_ZuoZhe(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_MAX_NUMBER,
                           redispool_number=config.REDIS_POOL_MAX_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.get_eval(task)
        # print(task_data)
        url = task_data['url']
        sha = task_data['sha']
        name = task_data['name']
        shijian = task_data.get('shiJian')

        # 获取会议主页html源码
        resp = self.__getResp(url=url, method='GET')

        # with open('article.html', 'w', encoding='utf-8') as f:
        #     f.write(resp.text)

        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PEOPLE, sha=sha)
            return

        article_html = resp.text
        # 判断是否是有效页面
        html_status = self.server.ifEffective(article_html)
        if html_status:
            # ========================获取数据==========================
            # 获取标题
            save_data['title'] = name
            # 获取所在单位
            save_data['suoZaiDanWei'] = self.server.getSuoZaiDanWei(article_html, shijian)
            # 获取关联企业机构
            save_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)

            # url
            save_data['url'] = url
            # 生成key
            save_data['key'] = url
            # 生成sha
            save_data['sha'] = sha
            # 生成ss ——实体名称
            save_data['ss'] = '人物'
            # 生成es ——栏目名称
            save_data['es'] = '论文'
            # 生成ws ——网站名称
            save_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            save_data['clazz'] = '人物_论文作者'
            # 生成biz ——项目名称
            save_data['biz'] = '文献大数据_论文'
            # 生成ref
            save_data['ref'] = ''

            # --------------------------
            # 存储部分
            # --------------------------
            # 保存机构队列
            if save_data['guanLianQiYeJiGou']:
                jigouList = copy.deepcopy(save_data['guanLianQiYeJiGou'])
                for jigou in jigouList:
                    jigou['name'] = jigou['name'].replace('"', '\\"').replace("'", "''")
                    jigou['url'] = jigou['url'].replace('"', '\\"').replace("'", "''")
                    self.dao.save_task_to_mysql(table=config.MYSQL_INSTITUTE, memo=jigou, ws='中国知网', es='论文')

            return sha

        else:
            LOGGING.error('对不起，未找到相关数据，url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PEOPLE, sha=sha)

    def run(self, task):
        # 创建数据存储字典
        save_data = {}
        # 获取字段值存入字典并返回sha
        sha = self.handle(task=task, save_data=save_data)
        # 保存数据到Hbase
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        # 存储数据
        success = self.dao.save_data_to_hbase(data=save_data)
        if success:
            # 删除任务
            self.dao.delete_task_from_mysql(table=config.MYSQL_PEOPLE, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_PEOPLE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.get_task_from_redis(key=config.REDIS_ZHIWANG_PEOPLE, count=50, lockname=config.REDIS_ZHIWANG_PEOPLE_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)

            else:
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"name": "康微", "url": "http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield=au&skey=康微&code=33288882", "sha": "134e9400821993c5245f6c6f493ba4014dbe869c", "ss": "人物", "shiJian": {"Y": 2013, "M": 11, "D": 1}}')
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))