# -*-coding:utf-8-*-
'''
HBase连接池操作
'''

import sys
import os
import happybase

# sys.path.append(os.path.dirname(__file__) + os.sep + "../")
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../")))


class HBasePool(object):
    def __init__(self):
        # 创建连接，通过参数size来设置连接池中连接的个数
        self.pool = happybase.ConnectionPool(size=5, # 连接池中连接个数
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

    # 获取一行数据
    def get_datas(self, row_key):
        with self.pool.connection() as connection:
            # print(connection.tables())
            table = happybase.Table('media:document', connection)
            # print(table.families())
            info = table.row(row_key, columns=None, include_timestamp=False)
            return info


if __name__ == '__main__':
    hb = HBasePool()
    hb.get_datas('ef4c10c09147242b65750a77c2b8d28d8a579147')

