# -*- coding:utf-8 -*-
from loguru import logger


class Logger(object):
    def __init__(self, file_dir, log_name):
        # log输出格式
        logger_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {process} {thread} {level} - {message}"
        # 输出到指定目录下的log文件，并按天分隔
        logger.add("/opt/Log/%s/%s_{time}.log" % (file_dir, log_name),
                   format=logger_format,
                   level="INFO",
                   rotation='00:00',
                   retention='30 days',
                   # compression='zip',
                   enqueue=True,
                   encoding="utf-8")

    @staticmethod
    def log(msg):
        logger.log('INFO', msg)

    @staticmethod
    def debug(msg):
        logger.debug(msg)

    @staticmethod
    def info(msg):
        logger.info(msg)

    @staticmethod
    def warning(msg):
        logger.warning(msg)

    @staticmethod
    def error(msg):
        logger.error(msg)

    @staticmethod
    def exception(e):
        logger.exception(str(e))


if __name__ == '__main__':
    logging = Logger("TestCase", '论文_data')
    logging.info('你好')
    logging.log('Hello')
    logging.exception('程序报错')
