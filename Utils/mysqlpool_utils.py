# -*-coding:utf-8-*-
'''
mysql连接池操作
'''

import sys
import os
import pymysql
from DBUtils.PooledDB import PooledDB

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings


DB_HOST=settings.DB_HOST
DB_PORT=settings.DB_PORT
DB_USER=settings.DB_USER
DB_PASS=settings.DB_PASS
DB_NAME=settings.DB_NAME
DB_POOL_MIN_NUMBER=settings.DB_POOL_MIN_NUMBER
DB_POOL_MAX_NUMBER=settings.DB_POOL_MAX_NUMBER
DB_POOL_MAX_CONNECT=settings.DB_POOL_MAX_CONNECT


def createMysqlPool():
    # 创建mysql连接池
    pool = PooledDB(
                    pymysql,
                    mincached=DB_POOL_MIN_NUMBER, # 最小空闲连接数
                    maxcached=DB_POOL_MAX_NUMBER, # 最大空闲连接数
                    maxconnections=DB_POOL_MAX_CONNECT, # 最大连接数
                    blocking=True,
                    host=DB_HOST,
                    user=DB_USER,
                    passwd=DB_PASS,
                    db=DB_NAME,
                    port=DB_PORT,
                    charset="utf8mb4",
                    cursorclass=pymysql.cursors.DictCursor # 以字典格式返回数据
                    )

    return pool


def _do_in_cursor(callback, pool):
    conn = None
    try:
        conn = pool.connection()
        cursor = conn.cursor()
        result = callback(cursor)
        conn.commit()
        cursor.close()
        return result

    finally:
        if conn:
            conn.close()

# 执行一条sql语句
def execute(connection, sql):
    def run(cursor):
        try:
            res = cursor.execute(sql)
            return res
        except:

            return None

    return _do_in_cursor(run, connection)

# 查询所有结果
def get_results(connection, sql):
    '''
    :param connection: 链接池对象
    :param sql: sql查询语句
    :return: [{}, {}, {}...]
    '''
    def run(cursor):
        try:
            cursor.execute(sql)
            res = cursor.fetchall()
            return res
        except:

            return []

    return _do_in_cursor(run, connection)

# 查询一个结果
def get_result(connection, sql):
    '''
    :param connection: 连接池对象
    :param sql: sql查询语句
    :return: {}
    '''
    def run(cursor):
        try:
            cursor.execute(sql)
            res = cursor.fetchone()
            return res
        except:

            return {}

    return _do_in_cursor(run, connection)

# 插入一条数据
def insert_one(connection, table, data):
    '''
    :param connection: 连接池对象
    :param table: 表名
    :param data: 要插入的数据｛key: value｝
    '''
    def run(cursor):
        name = []
        value = []

        for key in data:
            name.append(key)
            value.append(data[key])

        sql = "insert into {table}(`{name}`) VALUES ('{value}')".format(table='`' + table + '`',
                                                                      name='`,`'.join(str(n) for n in name),
                                                                      value='\',\''.join(str(v) for v in value))
        cursor.execute(sql)

    return _do_in_cursor(run, connection)

# 更新数据
def update(connection, table, data, where):
    '''
    :param connection: 链接池对象
    :param table: 表名
    :param data: 要修改的数据　{key: value}
    :param where: 判断语句
    '''
    def run(cursor):
        updates = []

        for key in data:
            index = "{}='{}'".format(key, data[key])
            updates.append(index)

        sql = "update `{}` set {} WHERE {}".format(table, ','.join(updates), where)

        print(sql)

        cursor.execute(sql)

    return _do_in_cursor(run, connection)
