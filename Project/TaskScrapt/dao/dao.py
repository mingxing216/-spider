# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage


class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    def getCateidList(self, table):
        sql = 'select cateid from {} group by `cateid`'.format(table)
        return self.mysql_client.get_results(sql=sql)

    def getTaskNumber_Redis(self, cateid_pinyin):
        return self.redis_client.scard(cateid_pinyin)

    def getM_Task(self, table, cateid):
        sql = "select memo from {} where `cateid` = '{}' and `del` = '0' and `err` = '0' limit 10000".format(table, cateid)
        return self.mysql_client.get_results(sql=sql)

    def insertTaskToRedis(self, key, m_task):
        if not m_task:
            return

        for task_data in m_task:
            task = task_data['memo']

            self.redis_client.sadd(key=key, value=task)

        self.logging.info('Add {} task success number: {}'.format(key, len(m_task)))