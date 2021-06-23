# -*- coding:utf-8 -*-
"""

"""

import sys
import os
import copy

import pymysql

from Utils import timeutils
from Storage import storage


class Dao(storage.Dao):
    def __init__(self, logging, host, port, user, pwd, db, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  host=host, port=port, user=user, pwd=pwd, db=db,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    # 期刊年卷期信息批量登记到mysql表中
    def record_one_journal_info_to_mysql(self, table, data_list, key):
        self.timer.start()
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `id` = '{}'".format(table, key)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if data_status:
            self.logging.warning('mysql | Mysql表中已存在 | use time: {} | id: {}'.format(self.timer.use_time(), key))
        else:
            date = timeutils.get_now_datetime()
            data_list.append(date)
            data_list.append(date)

            journal_field = ['ws', 'create_owner', 'url', 'year', 'journal_id', 'issue', 'id', 'created', 'updated']
            sql = "insert into {table} ({name}) values ('{value}')".format(
                table=table, name=', '.join(journal_field), value="', '".join(pymysql.escape_string(str(v)) for v in data_list))

            self.mysql_client.execute_one(sql)
            self.logging.info('mysql | 已存入到Mysql表中 | use time: {} | id: {}'.format(self.timer.use_time(), key))

    # 更新mysql存储表状态
    def update_journal_info_to_mysql(self, table, ws, journal_id, year, issue):
        self.timer.start()
        sql = "update {} set `stat` = 2, `updated` = now() where `ws` = '{}' and `journal_id` = '{}' and `year` = '{}' and `issue` = '{}'".format(
            table, ws, journal_id, year, issue)

        self.mysql_client.execute_one(sql)
        self.logging.info('mysql | 已更改Mysql表状态, {} {} {} | use time: {}'.format(year, journal_id, issue, self.timer.use_time()))

    # 获取期刊年卷期信息
    def get_journal_info_from_mysql(self, table, ws, journal_id):
        self.timer.start()
        sql = "select `year`, `issue` from {} where `ws` = '{}' and `journal_id` = '{}'".format(table, ws, journal_id)

        data_list = self.mysql_client.get_results(sql=sql)
        self.logging.info('mysql | 已从Mysql获取到 {} 条年卷期 | use time: {}'.format(len(data_list), self.timer.use_time()))

        return data_list
