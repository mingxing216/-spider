# -*-coding:utf-8-*-

import os
import sys
import time
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Utils import redispool_utils
from Utils import mysqlpool_utils
from Project.WanFangZhuanLi.dao import dao


class Main(object):
    def __init__(self):
        pass

    def run(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        while True:
            # 查询万方redis任务队列数量
            number = dao.getRedisPatentUrlNumber(redis_client=redis_client)
            if number <= 100:
                # 从mysql中获取1000个任务
                url_for_mysql = dao.getPatentUrl_1000(connection=mysql_client)
                if url_for_mysql:
                    for url_data in url_for_mysql:
                        # 将任务队列至redis
                        dao.input_patent_url_to_redis(redis_client, json.dumps(url_data))
                else:
                    time.sleep(10)
                    continue

            else:
                time.sleep(10)
                continue
            # break


if __name__ == '__main__':
    m = Main()
    m.run()
