# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import re
import hashlib
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_论文_会议数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.ZhiWangLunWen_HuiYiDataDownloader(logging=LOGGING,
                                                                                         proxy_type=config.PROXY_TYPE,
                                                                                         timeout=config.TIMEOUT,
                                                                                         proxy_country=config.COUNTRY)
        self.server = service.ZhiWangLunWen_HuiYiDataServer(logging=LOGGING)
        self.dao = dao.ZhiWangLunWen_HuiYiDataDao(logging=LOGGING,
                                                  mysqlpool_number=config.MYSQL_POOL_NUMBER,
                                                  redispool_number=config.REDIS_POOL_NUMBER)




class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 获取task数据
        task = self.server.getTask(task_data)
        try:
            url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?' + re.findall(r"\?(.*)", task['url'])[0]
            # url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?pcode=CIPD&lwjcode=FYHS201812001&hycode=026425'
            # print(url)
        except:
            url = None
        if not url:
            return
        # url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?pcode=CIPD&lwjcode=JCFS201212001&hycode='
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        jibie = task['jibie']
        return_data = {}
        # 获取会议主页html源码
        article_html = self.download_middleware.getResp(url=url, mode='get')
        # print(article_html['data'])
        if article_html['status'] == 0:
            article_html = article_html['data'].content.decode('utf-8')
            # ========================获取数据==========================
            # 获取标题
            return_data['title'] = self.server.getTitle(resp=article_html, text='会议名称')
            # 获取举办时间
            # return_data['juBanShiJian'] = self.server.getField(resp=article_html, text='会议时间') + ' ' + '00:00:00'
            jubanshijian = self.server.getField(resp=article_html, text='会议时间')
            return_data['juBanShiJian'] = timeutils.getDateTimeRecord(jubanshijian)
            # 获取所在地_内容
            return_data['suoZaiDiNeiRong'] = self.server.getField(resp=article_html, text='会议地点')
            # 获取主办单位
            return_data['zhuBanDanWei'] = self.server.getTitle(resp=article_html, text='学会名称')
            # 获取级别
            return_data['jiBie'] = jibie

            # 获取关联主办单位
            return_data['guanLianZhuBanDanWei'] = ''

            # url
            return_data['url'] = url
            # 生成key
            return_data['key'] = url
            # 生成sha
            return_data['sha'] = sha
            # 生成ss ——实体
            return_data['ss'] = '活动'
            # 生成ws ——目标网站
            return_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            return_data['clazz'] = '活动_会议'
            # 生成es ——栏目名称
            return_data['es'] = '会议文集'
            # 生成biz ——项目
            return_data['biz'] = '文献大数据'
            # 生成ref
            return_data['ref'] = ''
            # --------------------------
            # 存储部分
            # --------------------------

            # 保存数据
            self.dao.saveDataToHbase(data=return_data)

        else:
            LOGGING.error('获取文章页html源码失败，url: {}'.format(url))

    def start(self):
        # # 从论文队列获取论文任务
        # task_list = self.dao.getWenJiUrls()
        #
        # if task_list:
        #     thread_pool = ThreadPool()
        #     for task in task_list:
        #         thread_pool.apply_async(func=self.handle, args=(task,))
        #         # break
        #     thread_pool.close()
        #     thread_pool.join()

        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_HUIYILUNWEN_QIKAN, count=100, lockname=config.REDIS_HUIYILUNWEN_QIKAN_LOCK)
            # print(task_list)
            # print(len(task_list))
            LOGGING.info('从redis获取{}个任务'.format(len(task_list)))

            # 创建线程池
            threadpool = ThreadPool()
            for task in task_list:
                threadpool.apply_async(func=self.handle, args=(task,))

            # task = task_list[0]
            # threadpool.apply_async(func=self.handle, args=(task,))

            threadpool.close()
            threadpool.join()

            time.sleep(3)


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANGLUNWEN_HUIYIDATA_PROCESS_NUMBER)
    for i in range(config.ZHIWANGLUNWEN_HUIYIDATA_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
