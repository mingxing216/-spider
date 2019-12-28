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
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网论文_文集数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.ZhiWangLunWen_WenJiDataDownloader(logging=LOGGING,
                                                                                         proxy_type=config.PROXY_TYPE,
                                                                                         timeout=config.TIMEOUT,
                                                                                         proxy_country=config.COUNTRY)
        self.server = service.ZhiWangLunWen_WenJiDataServer(logging=LOGGING)
        self.dao = dao.ZhiWangLunWen_WenJiDataDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 获取task数据
        task = self.server.getTask(task_data)
        print(task)

        return_data = {}

        try:
            url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?' + re.findall(r"\?(.*)", task['url'])[0]
        except:
            url = None
        if not url:
            return

        # url = 'http://navi.cnki.net/knavi/DpaperDetail/CreateDPaperBaseInfo?pcode=CIPD&lwjcode=DNKF200908001&hycode=009789'

        # 获取会议主页html源码
        article_html = self.download_middleware.getResp(url=url, mode='get')
        if article_html['status'] == 0:
            article_html = article_html['data'].content.decode('utf-8')
            # ========================获取数据==========================
            # 获取标题
            return_data['title'] = self.server.getTitle(article_html)
            # 获取标识
            return_data['biaoShi'] = self.server.getBiaoShi(article_html)
            # 获取出版单位
            return_data['chuBanDanWei'] = self.server.getField(resp=article_html, text='出版单位')
            # 获取出版时间
            return_data['chuBanShiJian'] = self.server.getField(resp=article_html, text='出版日期')
            # 获取主编
            return_data['zhuBian'] = self.server.getField(resp=article_html, text='主编')
            # 获取编者
            return_data['bianZhe'] = self.server.getField(resp=article_html, text='编者')
            # 获取专辑名称
            return_data['zhuanJiMingCheng'] = self.server.getField(resp=article_html, text='专辑名称')
            # 获取专题名称
            return_data['zhuanTiMingCheng'] = self.server.getField(resp=article_html, text='专题名称')
            # 获取关联活动_会议
            return_data['guanLianHuoDong_HuiYi'] = self.server.getGuanLianHuoDong_HuiYi(url, '活动')

            # url
            return_data['url'] = url
            # 生成key
            return_data['key'] = url
            # 生成sha
            return_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
            # 生成ss ——实体
            return_data['ss'] = '期刊'
            # 生成ws ——目标网站
            return_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            return_data['clazz'] = '期刊_会议文集'
            # 生成es ——栏目名称
            return_data['es'] = '会议文集'
            # 生成biz ——项目
            return_data['biz'] = '文献大数据'
            # 生成ref
            return_data['ref'] = ''

            # --------------------------
            # 存储部分
            # --------------------------
            # 保存媒体url
            if return_data['biaoShi']:
                self.dao.saveMediaToMysql(url=return_data['biaoShi']['url'], type='image')
            # 保存数据
            self.dao.saveDataToHbase(data=return_data)

        else:
            LOGGING.error('获取文章页html源码失败，url: {}'.format(url))

    def start(self):
        while True:
            # 从文集redis队列中获取100个文集任务
            # task_list = self.dao.getQiKanUrls()
            task_list = self.dao.getTask(key=config.REDIS_HUIYILUNWEN_WENJI, count=100,
                                         lockname=config.REDIS_HUIYILUNWEN_WENJI_LOCK)
            # print(task_list)
            # print(len(task_list))
            if task_list:
                thread_pool = ThreadPool()
                for task in task_list:
                    thread_pool.apply_async(func=self.handle, args=(task,))
                    break
                thread_pool.close()
                thread_pool.join()
            else:
                LOGGING.warning('任务队列暂无数据。')
                time.sleep(10)

            # break


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANGLUNWEN_WENJIDATA_PROCESS_NUMBER)
    for i in range(config.ZHIWANGLUNWEN_WENJIDATA_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
