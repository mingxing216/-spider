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
            self.logging.error('hbase | row获取数据失败 | use time: {}'.format(self.timer.use_time()))
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
            self.logging.error('hbase | msg: {} | key: {}'.format(e, row_key))
            return

    def get_datas_from_hbase(self, table, row_key_list, columns=None):
        self.timer.start()
        self.logging.debug('hbase | 开始获取数据')
        res = self._get_datas_from_hbase(table, row_key_list, columns=columns)
        if res is not None:
            self.logging.info('hbase | rows获取数据成功 | use time: {} | count: {}'.format(self.timer.use_time(), len(res)))
        else:
            self.logging.error('hbase | rows获取数据失败 | use time: {} | count: {}'.format(self.timer.use_time(), len(row_key_list)))
        self.logging.debug('hbase | 结束获取数据')

        return res

    # 获取hbase数据
    def _get_datas_from_hbase(self, table, row_key_list, columns=None):
        data_list = []
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                tab = happybase.Table(table, connection)
                # print(table.families())
                rows_data = tab.rows(row_key_list, columns=columns, include_timestamp=False)
                # print(info)
                for row, datas in rows_data:
                    data = dict()
                    for key, value in datas.items():
                        data[key.decode("utf-8")] = value.decode('utf-8')
                    data_list.append((row.decode("utf-8"), data))

                return data_list

        except Exception as e:
            self.logging.error('hbase | msg: {} | key: {}'.format(e, row_key_list))
            return

    # 删除hbase数据
    def delete_one_data_from_hbase(self, table, row_key):
        self.timer.start()
        self.logging.debug('hbase | 开始删除数据')
        try:
            with self.pool.connection() as connection:
                # print(connection.tables())
                tab = happybase.Table(table, connection)
                # 删除一整行数据
                tab.delete(row_key)
                self.logging.info('hbase | 数据删除成功 | use time: {}'.format(self.timer.use_time()))
                return True

        except Exception as e:
            self.logging.error('hbase | 数据删除失败 | use time: {} | msg: {} | key: {}'.format(self.timer.use_time(), e, row_key))
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
                    data_list.append((row.decode("utf-8"), data))

                self.logging.info('hbase | scan获取数据成功 | use time: {} | count: {}'.format(self.timer.use_time(), len(data_list)))
                return data_list

        except Exception as e:
            self.logging.error("hbase | scan获取数据失败 | use time: {} | key: {} | msg: {}".format(self.timer.use_time(), row_start, e))
            return


if __name__ == '__main__':
    hb = HBasePool('localhost')
    hb.get_one_data_from_hbase('ef4c10c09147242b65750a77c2b8d28d8a579147')
    query = "SingleColumnValueFilter('s', 'ws', =, 'substring:中国知网') AND SingleColumnValueFilter('s', 'es', =, 'substring:期刊论文') AND SingleColumnValueFilter('d', 'metadata_version', =, 'substring:V1', true, true)"
    data_list = hb.scan_from_hbase(table='ss_paper', row_start='978f699b266058247419843f5fce5036e1521e56', limit=2, query=query)
    for data in data_list:
        print(data[1].get('d:keyword', '[]'))
        print(data[1].get('d:keyword', '[]').replace('\\', ''))
        keyword = json.loads(data[1].get('d:keyword', '[]').replace('\\', ''))
        print(keyword)
        print(data[1].get('d:abstract', '[]'))
        print(data[1].get('d:abstract', '[]').replace('\\', ''))
        abstract = json.loads(data[1].get('d:abstract', '[]'))
        print(abstract)
