# -*-coding:utf-8-*-
'''
HBase连接池操作
'''

import sys
import os
import time
import happybase


class HBasePool(object):
    def __init__(self, logging=None):
        self.logging = logging
        # 创建连接池，通过参数size来设置连接池中连接的个数
        self.pool = happybase.ConnectionPool(size=32, # 连接池中连接个数
                                             host="mm-node5",
                                             # port=9090,
                                             # timeout=20,
                                             autoconnect=True, # 连接是否直接打开
                                             # table_prefix=None, # 用于构造表名的前缀
                                             # table_prefix_separator=b'_', # 用于table_prefix的分隔符
                                             # compat='0.98', # 兼容模式
                                             transport='framed', # 运输模式
                                             protocol='compact' # 协议
                                            )

    def get_one_data_from_hbase(self, row_key):
        start_time = time.time()
        self.logging.info('开始获取全文')
        res = self._get_one_data_from_hbase(row_key)
        if res is not None:
            self.logging.info('handle | 全文获取成功 | use time: {}'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 全文获取失败 | use time: {}'.format('%.3f' % (time.time() - start_time)))
        self.logging.info('结束获取全文')

        return res

    # 获取hbase数据
    def _get_one_data_from_hbase(self, row_key):
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                table = happybase.Table('media:document', connection)
                # print(table.families())
                info = table.row(row_key, columns=None, include_timestamp=False)
                # print(info)
                return info

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key))
            return

    def get_datas_from_hbase(self, row_key_list):
        start_time = time.time()
        self.logging.info('开始获取全文')
        res = self._get_datas_from_hbase(row_key_list)
        if res is not None:
            self.logging.info('handle | {} 条全文获取成功 | use time: {}'.format(len(res), '%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | {} 条全文获取失败 | use time: {}'.format(len(row_key_list), '%.3f' % (time.time() - start_time)))
        self.logging.info('结束获取全文')

        return res

    # 获取hbase数据
    def _get_datas_from_hbase(self, row_key_list):
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                table = happybase.Table('media:document', connection)
                # print(table.families())
                info = table.rows(row_key_list, columns=None, include_timestamp=False)
                # print(info)
                return info

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key_list))
            return

    def delete_one_data_from_hbase(self, row_key):
        start_time = time.time()
        self.logging.info('开始删除全文')
        res = self._delete_one_data_from_hbase(row_key)
        if res:
            self.logging.info('handle | 全文删除成功 | use time: {}'.format('%.3f' % (time.time() - start_time)))
        else:
            self.logging.info('handle | 全文删除失败 | use time: {}'.format('%.3f' % (time.time() - start_time)))

        self.logging.info('结束删除全文')

        return res

    # 删除hbase数据
    def _delete_one_data_from_hbase(self, row_key):
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                table = happybase.Table('media:document', connection)
                # 删除一整行数据
                table.delete(row_key)
                return True

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key))
            return False


if __name__ == '__main__':
    hb = HBasePool()
    hb.get_one_data_from_hbase('ef4c10c09147242b65750a77c2b8d28d8a579147')
