# -*- coding: utf-8 -*-
'''
本文件提供mysql数据库操作公共方法
'''

import pymysql
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../")

import settings


class DBUtils_PyMysql(object):

    def get_connection(self):
        conn = pymysql.connect(host=settings.DB_HOST,
                               user=settings.DB_USER,
                               password=settings.DB_PASS,
                               database=settings.DB_NAME,
                               port=settings.DB_PORT,
                               charset="utf8mb4",
                               cursorclass=pymysql.cursors.DictCursor)
        return conn

    def _do_in_cursor(self, func):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            result = func(cursor)
            conn.commit()
            cursor.close()
            return result

        finally:
            if conn:
                conn.close()

    # 查询所有结果
    def get_results(self, sql):
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

        return self._do_in_cursor(run)

    # 查询一个结果
    def get_result(self, sql):
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

        return self._do_in_cursor(run)

    # 插入一条数据
    def insert_one(self, table, data):
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
                                                                            value='\',\''.join(
                                                                                str(v) for v in value))

            cursor.execute(sql)

        return self._do_in_cursor(run)

    # 更新数据
    def update(self, table, data, where):
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

            cursor.execute(sql)

        return self._do_in_cursor(run)


if __name__ == '__main__':
    du = DBUtils_PyMysql()
    data = du.get_result('select * from ss_paper where sha = "0019f7b069e8fa17a6693db3ebc46ba5cee588ff"')
    print(data)


    # def get_result(self, sql):
    #     '''
    #     查询满足条件的一条数据
    #     :param sql: sql语句
    #     :return: 字典类型查询结果
    #     '''
    #     conn = self.get_connection()
    #     cur = conn.cursor()
    #     cur.execute(sql)
    #     ret = cur.fetchone()
    #     cur.close()
    #     conn.close()
    #
    #     return ret
    #
    # def get_results(self, sql):
    #     '''
    #     查询满足条件的所有数据
    #     :param sql: sql语句
    #     :return: 字典类型查询结果
    #     '''
    #     conn = self.get_connection()
    #     cur = conn.cursor()
    #     cur.execute(sql)
    #     ret = cur.fetchall()
    #     cur.close()
    #     conn.close()
    #
    #     return ret
    #
    # def insertOne(self, sql):
    #     '''
    #     插入一条数据， 并返回被插入数据的主键ID
    #     :param sql: sql语句
    #     :return: 被插入数据的主键ID
    #     '''
    #     conn = self.get_connection()
    #     cur = conn.cursor()
    #     ret = cur.execute(sql)
    #     if ret != 0:
    #         keyword_id = cur.lastrowid
    #         conn.commit()
    #         cur.close()
    #         conn.close()
    #
    #         return keyword_id
    #
    #     else:
    #         conn.rollback()
    #         cur.close()
    #         conn.close()
    #
    # def insertInTo(self, sql):
    #     '''
    #     插入数据， 不返回结果
    #     :param sql: 存储sql语句
    #     '''
    #     conn = self.get_connection()
    #     cur = conn.cursor()
    #     ret = cur.execute(sql)
    #     if ret != 0:
    #         conn.commit()
    #         cur.close()
    #         conn.close()
    #     else:
    #         conn.rollback()
    #         cur.close()
    #         conn.close()
    #
    # def update(self, sql):
    #     '''
    #     更新数据
    #     :param sql: sql语句
    #     '''
    #     conn = self.get_connection()
    #     cur = conn.cursor()
    #     ret = cur.execute(sql)
    #     if ret != 0:
    #         conn.commit()
    #
    #     else:
    #         conn.rollback()
    #     cur.close()
    #     conn.close()
    #     return int(ret)