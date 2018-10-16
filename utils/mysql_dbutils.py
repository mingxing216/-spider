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

    def get_result(self, sql):
        '''
        查询满足条件的一条数据
        :param sql: sql语句
        :return: 字典类型查询结果
        '''
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchone()
        cur.close()
        conn.close()

        return ret

    def get_results(self, sql):
        '''
        查询满足条件的所有数据
        :param sql: sql语句
        :return: 字典类型查询结果
        '''
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchall()
        cur.close()
        conn.close()

        return ret

    def insertOne(self, sql):
        '''
        插入一条数据， 并返回被插入数据的主键ID
        :param sql: sql语句
        :return: 被插入数据的主键ID
        '''
        conn = self.get_connection()
        cur = conn.cursor()
        ret = cur.execute(sql)
        if ret != 0:
            keyword_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()

            return keyword_id

        else:
            conn.rollback()
            cur.close()
            conn.close()

    def insertInTo(self, sql):
        '''
        插入数据， 不返回结果
        :param sql: 存储sql语句
        '''
        conn = self.get_connection()
        cur = conn.cursor()
        ret = cur.execute(sql)
        if ret != 0:
            conn.commit()
            cur.close()
            conn.close()
        else:
            conn.rollback()
            cur.close()
            conn.close()

    def update(self, sql):
        '''
        更新数据
        :param sql: sql语句
        '''
        conn = self.get_connection()
        cur = conn.cursor()
        ret = cur.execute(sql)
        if ret != 0:
            conn.commit()

        else:
            conn.rollback()
        cur.close()
        conn.close()
        return int(ret)