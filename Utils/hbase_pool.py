# -*-coding:utf-8-*-
'''
HBase连接池操作
'''

import sys
import os
import happybase

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings


class HBasePool(object):
    def __init__(self):
        # 创建连接，通过参数size来设置连接池中连接的个数
        self.pool = happybase.ConnectionPool(size=5, # 连接池中连接个数
                                             host="60.195.249.127",
                                             # port=10000,
                                             timeout=20,
                                             autoconnect=True # 连接是否直接打开
                                             # table_prefix=None, # 用于构造表名的前缀
                                             # table_prefix_separator=b'_', # 用于table_prefix的分隔符
                                             # compat='0.98', # 兼容模式
                                             # transport='buffered', # 运输模式
                                             # protocol='binary' # 协议
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

    # 获取连接
    def get_connection(self):
        with self.pool.connection() as connection:
            print(connection.tables())

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
        '''
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

        return self._do_in_cursor(run, self.pool)

    # 查询一个结果
    def get_result(self, sql):
        '''
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

        return self._do_in_cursor(run, self.pool)

    # 插入一条数据
    def insert_one(self, table, data):
        '''
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
                                                                            value="','".join(pymysql.escape_string(str(v)) for v in value))
            # print(sql)

            cursor.execute(sql)

        return self._do_in_cursor(run, self.pool)

    # 更新数据
    def update(self, table, data, where):
        '''
        :param table: 表名
        :param data: 要修改的数据　{key: value}
        :param where: 判断语句
        '''
        def run(cursor):
            updates = []

            for key in data:
                index = "{}='{}'".format(key, pymysql.escape_string(data[key])) # 存数据库时，单双引号反斜杠转义，防止存储失败
                updates.append(index)

            sql = "update `{}` set {} WHERE {}".format(table, ','.join(updates), where)
            # print(sql)

            cursor.execute(sql)

        return self._do_in_cursor(run, self.pool)

if __name__ == '__main__':
    hb = HBasePool()
    hb.get_connection()

