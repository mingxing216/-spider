# -*-coding:utf-8-*-
'''
mysql连接池操作
'''

import pymysql
from DBUtils.PooledDB import PooledDB

import settings


class MysqlPool(object):
    def __init__(self, number):
        # 创建mysql连接池
        self.pool = PooledDB(
            pymysql,
            mincached=2,  # 最小空闲连接数
            maxcached=5,  # 最大空闲连接数
            maxconnections=number,  # 最大连接数
            blocking=True,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            passwd=settings.DB_PASS,
            db=settings.DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor  # 以字典格式返回数据
        )

    def _do_in_cursor(self, callback, pool):
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
    def execute(self, sql):

        def run(cursor):
            try:
                res = cursor.execute(sql)
                return res
            except:

                return None

        return self._do_in_cursor(run, self.pool)

    # 查询所有结果
    def get_results(self, sql):
        """
        :param sql: sql查询语句
        :return: [{}, {}, {}...]
        """

        def run(cursor):
            try:
                cursor.execute(sql)
                res = cursor.fetchall()
                return res
            except:

                return []

        return self._do_in_cursor(run, self.pool)

    # 查询一个结果
    def get_result(self, sql):
        """
        :param sql: sql查询语句
        :return: {}
        """

        def run(cursor):
            try:
                cursor.execute(sql)
                res = cursor.fetchone()
                return res
            except:

                return {}

        return self._do_in_cursor(run, self.pool)

    # 插入一条数据
    def insert_one(self, table, data):
        """
        :param table: 表名
        :param data: 要插入的数据｛key: value｝
        """

        def run(cursor):
            name = []
            value = []

            for key in data:
                name.append(key)
                value.append(data[key])

            sql = "insert into {table}(`{name}`) VALUES ('{value}')".format(table='`' + table + '`',
                                                                            name='`,`'.join(str(n) for n in name),
                                                                            value="','".join(
                                                                                pymysql.escape_string(str(v)) for v in
                                                                                value))
            # print(sql)

            cursor.execute(sql)

        return self._do_in_cursor(run, self.pool)

    # 更新数据
    def update(self, table, data, where):
        """
        :param table: 表名
        :param data: 要修改的数据　{key: value}
        :param where: 判断语句
        """

        def run(cursor):
            updates = []

            for key in data:
                index = "{}='{}'".format(key, pymysql.escape_string(data[key]))  # 存数据库时，单双引号反斜杠转义，防止存储失败
                updates.append(index)

            sql = "update `{}` set {} WHERE {}".format(table, ','.join(updates), where)
            # print(sql)

            cursor.execute(sql)

        return self._do_in_cursor(run, self.pool)
