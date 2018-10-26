# -*-coding:utf-8-*-

'''
当前项目mysql操作模块
'''
import sys
import os
import pymysql
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from log import log
from utils import mysqlpool_utils
from utils import timeutils

logname = 'zhiwang_periodical'
logging = log.ILog(logname)


def getStatus(mysql_client, sha):
    '''
    查询当前文章是否被抓取过
    :param sha: 文章url sha1加密
    :return: True or False
    '''
    sql = "select sha from ss_paper where `sha` = '%s'" % sha
    status = mysqlpool_utils.get_results(connection=mysql_client, sql=sql)
    if status:

        return False
    else:

        return True

# 论文存储数据入库
def saveOrUpdate(mysql_client, sha, title, data):
    '''
    存储数据入库
    :param data: 爬虫发来的数据 
    return: 是否存储成功
    '''
    table = 'ss_paper'
    date_created = timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
    savedata = {
        'sha': sha,
        'title': title,
        'cat': 'paper',
        'clazz': '论文_期刊论文',
        'memo': pymysql.escape_string(data),
        'date_created': date_created
    }

    try:
        mysqlpool_utils.insert_one(connection=mysql_client, table=table, data=savedata)

    except:
        logging.info('insert_into error')

# 关联人物存储入库
def saveRenWu(mysql_client, sha, title, data):
    '''
    存储论文关联人物数据
    :param sha: 主键
    :param title: 人物名
    :param data: memo字段数据
    '''
    table = 'ss_people'
    savedata = {
        'sha': sha,
        'title': title,
        'cat': 'people',
        'clazz': '人物_论文作者',
        'memo': pymysql.escape_string(data),
        'date_created': timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
    }
    # 查询sql
    sql = "select memo from {} WHERE sha = '{}'".format(table, sha)
    # 查询库中是否含有此数据
    status = mysqlpool_utils.get_result(mysql_client, sql=sql)
    if not status:
        # 存储数据
        mysqlpool_utils.insert_one(connection=mysql_client, table=table, data=savedata)
    else:
        select_data = eval(status['memo'])
        # 数据库中的所在单位列表
        select_suoZaiDanWei = select_data['suoZaiDanWei']
        # 抓取到的所在单位列表
        insert_suoZaiDanWei = eval(data)['suoZaiDanWei']
        for danwei in insert_suoZaiDanWei:
            if danwei in select_suoZaiDanWei:

                continue
            else:

                select_suoZaiDanWei.append(danwei)

        select_data['suoZaiDanWei'] = select_suoZaiDanWei
        try:
            # 更新数据
            savedata['memo'] = pymysql.escape_string(json.dumps(select_data))
            savedata.pop('date_created')
            savedata['last_updated'] = timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
            mysqlpool_utils.update(connection=mysql_client, table=table, data=savedata, where="sha='{}'".format(sha))

        except Exception as e:
            print(e)

# 关联机构存储入库
def saveJiGou(mysql_client, sha, title, data):
    '''
    存储论文关联机构数据入库
    :param data: 爬虫输出数据
    :return: 
    '''
    table = 'ss_institute'
    date_created = timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
    savedata = {
        'sha': sha,
        'title': title,
        'cat': 'institute',
        'clazz': '机构_论文作者机构',
        'memo': pymysql.escape_string(data),
        'date_created': date_created
    }
    # 查询数据库是否存在当前数据
    select_sql = ("select sha from ss_institute where sha = '{}'".format(sha))
    status = mysqlpool_utils.get_results(connection=mysql_client, sql=select_sql)
    if status:
        savedata.pop('date_created')
        savedata['last_updated'] = date_created
        # 更新数据
        mysqlpool_utils.update(connection=mysql_client, table=table, data=savedata, where='sha = {}'.format(sha))

    else:
        mysqlpool_utils.insert_one(connection=mysql_client, table=table, data=savedata)
        logging.info('存储成功')

# 查看当前期刊是否被抓取过【期刊爬虫】
def selectQiKanStatus(mysql_client, sha):
    select_sql = "select sha from ss_magazine where `sha` = '%s'" % sha
    status = mysqlpool_utils.get_results(connection=mysql_client, sql=select_sql)
    if status:

        return False
    else:

        return True

# 关联期刊存储入库
def saveQiKan(mysql_client, sha, title, data):
    '''
    存储论文关联期刊数据入库
    :param data: 爬虫输出数据
    :return: 
    '''
    table = 'ss_magazine'
    savedata = {
        'sha': sha,
        'title': title,
        'cat': 'magazine',
        'clazz': '期刊_学术期刊',
        'memo': pymysql.escape_string(data),
        'date_created': timeutils.strDateToTime(timeutils.get_yyyy_mm_dd_hh_mm_ss())
    }

    # 查询数据库是否存在当前数据
    select_sql = ("select sha from ss_magazine where sha = '{}'".format(sha))
    data = mysqlpool_utils.get_results(connection=mysql_client, sql=select_sql)
    if not data:
        # 存储数据

        try:
            mysqlpool_utils.insert_one(connection=mysql_client, table=table, data=savedata)

            logging.info('insert_into OK')

        except Exception as e:
            logging.info(e)

