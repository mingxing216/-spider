# -*-coding:utf-8-*-

'''
当前项目mysql操作模块
'''
import sys
import os
import pymysql

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from log import log
from utils import mysql_dbutils
from utils import timeutils

logname = 'zhiwang_periodical'
logging = log.ILog(logname)


# 存储数据入库
def saveOrUpdate(sha, title, data):
    '''
    存储数据入库
    :param data: 爬虫发来的数据 
    return: 是否存储成功
    '''
    sql_server = mysql_dbutils.DBUtils_PyMysql()
    select_sql = "select * from ss_paper where `sha` = '%s'" % sha
    status = sql_server.get_results(select_sql)
    if status:
        last_updated = timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
        insert_data = pymysql.escape_string(data)
        sql = ("update ss_paper set `memo` = '%s', `last_updated` = '%s'" % (insert_data, last_updated))
        try:
            sql_server.insertInTo(sql)

        except:
            logging.info('update error')

    else:
        cat = 'paper'
        clazz = '论文_期刊论文'
        date_created = timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
        insert_data = pymysql.escape_string(data)
        sql = ("insert into "
               "ss_paper"
               "(`sha`, `title`, `cat`, `clazz`, `memo`, `date_created`) "
               "VALUES "
               "('%s', '%s', '%s', '%s', '%s', '%s')" % (sha, title, cat, clazz, insert_data, date_created))
        try:
            sql_server.insertInTo(sql)

        except:
            logging.info('insert_into error')



