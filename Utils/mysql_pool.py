# -*-coding:utf-8-*-
"""
mysql连接池操作
"""

import pymysql
from DBUtils.PooledDB import PooledDB

import settings
from Utils import timeutils


class MysqlPool(object):
    def __init__(self, number, logger=None):
        self.logger = logger
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

    # 从连接池获取一条连接
    @property
    def new_conn(self):
        self._conn = self.pool.connection()
        self._cursor = self._conn.cursor()

        return self._cursor

    # 释放连接
    def close(self):
        """释放连接归还给连接池"""
        self._cursor.close()
        self._conn.close()

    # 执行一条sql语句
    def _execute(self, sql):
        try:
            res = self.new_conn.execute(sql)
        except:
            res = None
        finally:
            self.close()

        return res

    # 查询所有结果
    def get_results(self, sql):
        """
        :param sql: sql查询语句
        :return: [{}, {}, {}...]
        """
        try:
            self.new_conn.execute(sql)
            res = self._cursor.fetchall()

        except:
            res = []

        finally:
            self.close()

        return res

    # 查询一个结果
    def get_result(self, sql):
        """
        :param sql: sql查询语句
        :return: {}
        """
        try:
            self.new_conn.execute(sql)
            res = self._cursor.fetchone()

        except:
            res = {}

        finally:
            self.close()

        return res

    # 插入一条数据
    def insert_one(self, table, data):
        """
        :param table: 表名
        :param data: 要插入的数据｛key: value｝
        """
        name = []
        value = []
        try:
            for key in data:
                name.append(key)
                value.append(data[key])

            sql = "INSERT INTO {table} ({name}) VALUES ('{value}')".format(table=table,
                                                                           name=','.join(str(n) for n in name),
                                                                           value="','".join(
                                                                                pymysql.escape_string(str(v)) for v in
                                                                                value))
            self.new_conn.execute(sql)
            self._conn.commit()

        except Exception as e:
            self.logger.error('sql | 执行错误: {}'.format(e))
            self._conn.rollback()

        finally:
            self.close()

    # 更新数据
    def update(self, table, data, where):
        """
        :param table: 表名
        :param data: 要修改的数据　{key: value}
        :param where: 判断语句
        """
        updates = []
        try:
            for key in data:
                index = "{}='{}'".format(key, pymysql.escape_string(data[key]))  # 存数据库时，单双引号反斜杠转义，防止存储失败
                updates.append(index)

            sql = "UPDATE {} SET {} WHERE {}".format(table, ','.join(updates), where)
            # print(sql)
            self.new_conn.execute(sql)
            self._conn.commit()

        except Exception as e:
            self.logger.error('sql | 执行错误: {}'.format(e))
            self._conn.rollback()

        finally:
            self.close()


if __name__ == '__main__':
    mysql_cli = MysqlPool(10)
    # sql = "select count(*) from job_paper where `ws` = '英文哲学社会科学' and `es` = '期刊论文' and `del` = '0';"
    sql = "select * from job_paper where ws = '英文哲学社会科学' and es = '期刊论文' and del = '0' limit 10"
    result = mysql_cli.get_results(sql)
    print(result)
    print(type(result))
    data = {
        'sha': 'qwerzxcvbb12345',
        'ctx': '{"test": "周杰伦", "test": "林俊杰", "test": "王力宏"}',
        'url': 'http://star',
        'es': '测试栏目',
        'ws': '测试网站',
        'msg': 'NULL',
        'date_created': timeutils.get_now_datetime()
    }
    mysql_cli.insert_one(table='job_paper', data=data)

    newdata = {
        'sha': '12345678987654321',
        'ctx': '{"hehe": "星", "xixi": "明", "haha": "亚", "gaga": "清"}',
        'url': 'http://haoxiangnimenya',
        'es': '更新栏目',
        'ws': '更新网站',
        'msg': 'NULL',
        'date_created': timeutils.get_now_datetime()
    }
    mysql_cli.update(table='job_paper', data=newdata, where="`sha` = '{}'".format('12345678987654321'))
