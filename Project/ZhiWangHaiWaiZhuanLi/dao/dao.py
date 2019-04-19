# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage


class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    # 保存任务url到mysql数据库
    def saveUrlToMysql(self, table, url):
        data = {
            'url': url
        }
        try:
            self.mysql_client.insert_one(table=table, data=data)
        except:
            pass

    # 查询redis数据库中有多少任务
    def selectTaskNumber(self, key):
        return self.redis_client.scard(key=key)

    # 从Mysql获取任务
    def getNewTaskList(self, table, count):
        sql = "select url from {} limit {}".format(table, count)

        return self.mysql_client.get_results(sql=sql)

    # 队列任务
    def QueueTask(self, key, data):
        if data:
            for url_data in data:
                url = url_data['url']
                self.redis_client.sadd(key=key, value=url)

        else:
            return

    # 从Mysql物理删除任务
    def deleteTask(self, table, url):
        sql = "delete from {} where url = '{}'".format(table, url)

        self.mysql_client.execute(sql=sql)