# -*-coding:utf-8-*-
"""
HBase连接池操作
"""
import json
import time
import happybase

from Utils import timers


class HBasePool(object):
    def __init__(self, host, logging=None):
        self.logging = logging
        self.timer = timers.Timer()
        # 创建连接池，通过参数size来设置连接池中连接的个数
        self.pool = happybase.ConnectionPool(size=32, # 连接池中连接个数
                                             host=host,
                                             # port=9090,
                                             # timeout=20,
                                             autoconnect=True, # 连接是否直接打开
                                             # table_prefix=None, # 用于构造表名的前缀
                                             # table_prefix_separator=b'_', # 用于table_prefix的分隔符
                                             # compat='0.98', # 兼容模式
                                             transport='framed', # 运输模式
                                             protocol='compact' # 协议
                                            )

    def get_one_data_from_hbase(self, table, row_key, columns=None):
        self.timer.start()
        self.logging.debug('hbase | 开始获取数据')
        res = self._get_one_data_from_hbase(table, row_key, columns=columns)
        if res is not None:
            self.logging.info('hbase | row获取数据成功 | use time: {}'.format(self.timer.use_time()))
        else:
            self.logging.info('hbase | row获取数据失败 | use time: {}'.format(self.timer.use_time()))
        self.logging.debug('hbase | 结束获取数据')

        return res

    # 获取hbase数据
    def _get_one_data_from_hbase(self, table, row_key, columns=None):
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                tab = happybase.Table(table, connection)
                # print(table.families())
                info = tab.row(row_key, columns=columns, include_timestamp=False)
                # print(info)
                data = dict()
                for key, value in info.items():
                    data[key.decode("utf-8")] = value.decode('utf-8')

                return data

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key))
            return

    def get_datas_from_hbase(self, table, row_key_list):
        self.timer.start()
        self.logging.debug('hbase | 开始获取数据')
        res = self._get_datas_from_hbase(table, row_key_list)
        if res is not None:
            self.logging.info('hbase | rows获取数据成功 | use time: {} | count: {}'.format(self.timer.use_time(), len(res)))
        else:
            self.logging.info('hbase | rows获取数据失败 | use time: {} | count: {}'.format(self.timer.use_time(), len(row_key_list)))
        self.logging.debug('hbase | 结束获取数据')

        return res

    # 获取hbase数据
    def _get_datas_from_hbase(self, table, row_key_list):
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                tab = happybase.Table(table, connection)
                # print(table.families())
                info = tab.rows(row_key_list, columns=None, include_timestamp=False)
                # print(info)
                return info

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key_list))
            return

    # 删除hbase数据
    def delete_one_data_from_hbase(self, row_key):
        self.timer.start()
        self.logging.debug('hbase | 开始删除数据')
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                table = happybase.Table('media:document', connection)
                # 删除一整行数据
                table.delete(row_key)
                self.logging.info('hbase | 数据删除成功 | use time: {}'.format(self.timer.use_time()))
                return True

        except Exception as e:
            self.logging.error('{} {}'.format(str(e), row_key))
            self.logging.error('hbase | 数据删除失败 | use time: {}'.format(self.timer.use_time()))
            return False

    # hbase scan 批量扫描数据
    def scan_from_hbase(self, table, limit=500, row_start=None, row_stop=None, query=None, columns=None):
        self.timer.start()
        self.logging.debug('hbase | 开始扫描数据')
        data_list = []
        try:
            with self.pool.connection() as connection:
                tab = happybase.Table(table, connection)
                scan_data = tab.scan(row_start=row_start, row_stop=row_stop, limit=limit, filter=query, columns=columns)
                for row, datas in scan_data:
                    data = dict()
                    for key, value in datas.items():
                        data[key.decode("utf-8")] = value.decode('utf-8')
                    res = json.dumps(data, ensure_ascii=False)

                    data_list.append((row.decode("utf-8"), res))

                self.logging.info('hbase | scan获取数据成功 | use time: {} | count: {}'.format(self.timer.use_time(), len(data_list)))
                return data_list

        except Exception as e:
            self.logging.error("hbase | {} | {}".format(row_start, e))
            return


if __name__ == '__main__':
    hb = HBasePool('mm-node5')
    hb.get_one_data_from_hbase('ef4c10c09147242b65750a77c2b8d28d8a579147')
    hb.scan_from_hbase('ss:paper')
