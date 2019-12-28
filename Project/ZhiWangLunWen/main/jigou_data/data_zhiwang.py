# -*-coding:utf-8-*-

'''

'''
import sys
import os
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
LOGNAME = '<知网论文_机构_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.ZhiWangLunWen_JiGouDataServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(10):
            resp = self.download_middleware.getResp(url=url,
                                                    mode=mode,
                                                    s=s,
                                                    data=data,
                                                    cookies=cookies,
                                                    referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 200:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            return None

    def handle(self, task, save_data):
        # 获取task数据
        task_data = self.server.evalTask(task)
        # print(task_data)

        sha = task_data['sha']
        url = task_data['url']
        # # 查询当前文章是否被抓取过
        status = self.dao.getTaskStatus(sha=sha)

        if status is False:
            # 获取会议主页html源码
            resp = self.__getResp(url=url, mode='get')
            # article_html = self.download_middleware.getResp(url='http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield=in&skey=%E4%B8%AD%E5%8C%97%E5%A4%A7%E5%AD%A6&code=0036109', mode='get')
            # print(article_html)

            if not resp:
                LOGGING.error('机构页面响应失败, url: {}'.format(url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)
                return

            article_html = resp.text
            # ========================获取数据==========================
            # 获取标题
            save_data['title'] = self.server.getJiGouName(article_html)
            # 获取曾用名
            save_data['cengYongMing'] = self.server.getCengYongMing(article_html)
            # 获取所在地_内容
            save_data['suoZaiDiNeiRong'] = self.server.getDiyu(article_html)
            # 获取主页(官网地址)
            save_data['zhuYe'] = self.server.getGuanWangDiZhi(article_html)
            # 获取标识(图片)
            save_data['biaoShi'] = self.server.getTuPian(article_html)

            # url
            save_data['url'] = url
            # 生成key
            save_data['key'] = url
            # 生成sha
            save_data['sha'] = sha
            # 生成ss ——实体
            save_data['ss'] = '机构'
            # 生成es ——栏目名称
            save_data['es'] = '论文'
            # 生成ws ——目标网站
            save_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            save_data['clazz'] = '机构_论文作者机构'
            # 生成biz ——项目
            save_data['biz'] = '文献大数据'
            # 生成ref
            save_data['ref'] = ''

            # 保存图片
            if save_data['biaoShi']:
                img_dict = {}
                img_dict['bizTitle'] = save_data['title']
                img_dict['relEsse'] = self.server.guanLianJiGou(url=url, sha=sha)
                img_dict['relPics'] = {}
                img_url = save_data['biaoShi']
                # # 存储图片种子
                # self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
                # 获取图片响应
                media_resp = self.__getResp(url=img_url,
                                            mode='GET')
                if not media_resp:
                    LOGGING.error('图片响应失败, url: {}'.format(img_url))
                    # 逻辑删除任务
                    self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
                    return

                img_content = media_resp.content
                # 存储图片
                self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')

            # # 记录已抓取任务
            # self.dao.saveComplete(table=config.MYSQL_REMOVAL, sha=sha)

        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)

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
        success = self.dao.saveDataToHbase(data=save_data)
        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_INSTITUTE, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_INSTITUTE, count=1, lockname=config.REDIS_INSTITUTE_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # # 创建gevent协程
                # g_list = []
                # for task in task_list:
                #     s = gevent.spawn(self.run, task)
                #     g_list.append(s)
                # gevent.joinall(g_list)

                # 创建线程池
                threadpool = ThreadPool()
                for url in task_list:
                    threadpool.apply_async(func=self.run, args=(url,))

                threadpool.close()
                threadpool.join()

                time.sleep(1)

            else:
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        # main.start()
        main.run(task='{"url": "http://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield=in&skey=%E5%AE%89%E5%BE%BD%E7%90%86%E5%B7%A5%E5%A4%A7%E5%AD%A6&code=0167619", "sha": "e4cdf4a7b733e8bca76b56c0048a0deea7c0dbb3"}')
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
