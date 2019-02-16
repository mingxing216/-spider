# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Project.XinHuaNews import config

if __name__ == '__main__':
    for data in config.COLUMN_INDEX_1:
        column_name = list(data.keys())[0]
        column_url = data[column_name]
        path = os.path.dirname(__file__) + os.sep + 'template_1.py'
        os.system('nohup python3 {} {} {} > /dev/null 2>&1 &'.format(path, column_name, column_url))







# from Log import log
# from Test.XinHuaNews.middleware import download_middleware
# from Test.XinHuaNews.service import service
# from Test.XinHuaNews.dao import dao
# from Test.XinHuaNews import config
#
# log_file_dir = 'XinHuaNews'  # LOG日志存放路径
# LOGNAME = '<新华网_时政>'  # LOG名
# LOGGING = log.ILog(log_file_dir, LOGNAME)
#
#
# class BastSpiderMain(object):
#     def __init__(self):
#         self.download_middleware = download_middleware.Downloader(logging=LOGGING,
#                                                                   update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
#                                                                   proxy_type=config.PROXY_TYPE,
#                                                                   timeout=config.TIMEOUT,
#                                                                   retry=config.RETRY,
#                                                                   proxy_country=config.COUNTRY)
#         self.server = service.Server(logging=LOGGING)
#         self.dao = dao.Dao(logging=LOGGING)
#
#
# class SpiderMain(BastSpiderMain):
#     def __init__(self):
#         super().__init__()
#
#
#     def start(self):
#         pass
#
#
# def process_start():
#     main = SpiderMain()
#     main.start()
#
# if __name__ == '__main__':
#     begin_time = time.time()
#     po = Pool(config.PROCESS_NUMBER)
#     for i in range(config.PROCESS_NUMBER):
#         po.apply_async(func=process_start)
#     po.close()
#     po.join()
#     end_time = time.time()
#     LOGGING.info('======The End!======')
#     LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
