# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
from multiprocessing.dummy import Pool as Thread_Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.Media_Object.middleware import download_middleware
from Project.Media_Object.service import service
from Project.Media_Object.dao import dao
from Project.Media_Object import config

log_file_dir = 'Media_Object'  # LOG日志存放路径
LOGNAME = '<媒体文件下载脚本>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, object_data):
        sha = object_data['sha']
        media_type = object_data['type']
        url = object_data['url']
        resp = self.download_middleware.getResp(url=url)
        if resp['status'] == 0:
            content = resp['data'].content
            # 保存数据到hbase
            save_status = self.dao.saveMediaToHbase(media_url=url,
                                                    content=content,
                                                    type=media_type).content.decode('utf-8')
            LOGGING.info('媒体文件已保存至hbase: {} | {}'.format(sha, url))
            # 删除mysql中object
            self.dao.delObject(sha=sha)

        else:
            LOGGING.error('媒体文件下载失败: {} | {}'.format(sha, url))
            # 删除mysql中object
            self.dao.delObject(sha=sha)

    def start(self):
        while 1:
            # 获取100个任务
            datas = self.dao.getObject(number=100)
            if not datas:
                time.sleep(10)
                LOGGING.info('数据库没任务了')
                continue
                
            thread_pool = Thread_Pool()
            for i in datas:
                thread_pool.apply_async(func=self.handle, args=(i,))
            thread_pool.close()
            thread_pool.join()


if __name__ == '__main__':
    main = SpiderMain()
    main.start()
