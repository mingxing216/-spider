# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网论文_作者数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.ZhiWangLunWen_ZuoZheDataDownloader(logging=LOGGING,
                                                                                          update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                                          proxy_type=config.PROXY_TYPE,
                                                                                          timeout=config.TIMEOUT,
                                                                                          retry=config.RETRY,
                                                                                          proxy_country=config.COUNTRY)
        self.server = service.ZhiWangLunWen_ZuoZheDataServer(logging=LOGGING)
        self.dao = dao.ZhiWangLunWen_ZuoZheDataDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 获取task数据
        task = self.server.getTask(task_data)
        sha = task['sha']
        url = task['url']
        name = task['name']
        return_data = {}
        # # 查询当前文章是否被抓取过
        status = self.dao.getZuoZheStatus(sha=sha)

        if status is False:
            # 获取会议主页html源码
            article_html = self.download_middleware.getResp(url=url, mode='get')
            if article_html['status'] == 0:
                article_html = article_html['data'].content.decode('utf-8')
                # ========================获取数据==========================
                # 获取所在单位
                return_data['suoZaiDanWei'] = self.server.getSuoZaiDanWei(article_html)
                # 获取关联企业机构
                return_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)
                return_data['name'] = name

                # url
                return_data['url'] = url
                # 生成key
                return_data['key'] = url
                # 生成sha
                return_data['sha'] = sha
                # 生成ss ——实体
                return_data['ss'] = '人物'
                # 生成ws ——目标网站
                return_data['ws'] = '中国知网'
                # 生成clazz ——层级关系
                return_data['clazz'] = '人物_论文作者'
                # 生成es ——栏目名称
                return_data['es'] = '论文作者'
                # 生成biz ——项目
                return_data['biz'] = '文献大数据'
                # 生成ref
                return_data['ref'] = ''

                # --------------------------
                # 存储部分
                # --------------------------
                # 保存机构队列
                self.dao.saveJiGouToMysql(return_data['guanLianQiYeJiGou'])
                # 记录已抓取任务
                self.dao.saveComplete(table=config.MYSQL_REMOVAL, sha=sha)
                # 删除任务
                self.dao.deleteZuoZheUrl(sha=sha)
                # 保存数据
                status = self.dao.saveDataToHbase(data=return_data)
                LOGGING.info(status.content.decode('utf-8'))

            else:
                LOGGING.error('获取文章页html源码失败，url: {}'.format(url))
                # 删除任务
                self.dao.deleteZuoZheUrl(sha=sha)

        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
            # 删除任务
            self.dao.deleteZuoZheUrl(sha=sha)

    def start(self):
        while True:
            # 从论文队列获取100个论文任务
            task_list = self.dao.getZuoZheUrls()

            if task_list:
                thread_pool = ThreadPool()
                for task in task_list:
                    thread_pool.apply_async(func=self.handle, args=(task,))
                    # break
                thread_pool.close()
                thread_pool.join()

            else:
                LOGGING.warning('任务队列暂无数据。')
                time.sleep(10)

                continue

            # break


def process_start():
    main = SpiderMain()
    main.start()


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANGLUNWEN_ZUOZHEDATA_PROCESS_NUMBER)
    for i in range(config.ZHIWANGLUNWEN_ZUOZHEDATA_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
