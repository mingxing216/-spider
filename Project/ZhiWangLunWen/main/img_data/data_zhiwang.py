# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
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
LOGNAME = '<知网论文_图片_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.ZhiWangLunWen_JiGou(logging=LOGGING)
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

    def imgDownload(self, img_task):
        # 数据类型转换
        task_data = self.server.getEvalResponse(img_task)
        # print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # 获取图片响应
        media_resp = self.__getResp(url=url, method='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(url))
            # # 标题内容调整格式
            # task_data['bizTitle'] = task_data['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储图片种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_IMG, memo=task_data, ws='中国知网', es='论文')

            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_IMG, sha=sha)
            return
        # media_resp.encoding = media_resp.apparent_encoding
        img_content = media_resp.content
        # 存储图片
        success = self.dao.save_media_to_hbase(media_url=url, content=img_content, item=task_data, type='image')
        if success:
            # 删除任务
            self.dao.delete_task_from_mysql(table=config.MYSQL_IMG, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_IMG, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.get_task_from_redis(key=config.REDIS_ZHIWNAG_IMG, count=50, lockname=config.REDIS_ZHIWNAG_IMG_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.imgDownload, task)
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
        # main.imgDownload(img_task='{"url": "http://image.cnki.net/getimage.ashx?id=JZCK2017070080003", "bizTitle": "基于侧试插件的采集控制Socket连接一且建立，在通信双方中的任何一方主动关闭连接之前，TCP连接都将被一直保持下去，通信双方即可开始相互发送数据内容，直到双方连接断开", "relEsse": {"url": "http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=JZCK201707008&tableName=CJFDLAST2017", "sha": "1808536c70dc383e7ddc0cc6d44f4e728a918ec1", "ss": "论文"}, "relPics": {"url": "http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=JZCK201707008&tableName=CJFDLAST2017", "sha": "1808536c70dc383e7ddc0cc6d44f4e728a918ec1", "ss": "组图"}}')
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
