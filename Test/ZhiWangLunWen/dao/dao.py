# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
import json

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Storage import storage


class HuiYiLunWen_LunWenTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(HuiYiLunWen_LunWenTaskDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getWenJiTask(self, table, data_type):
        sql = "select * from {} where `type` = '{}' and `del` = '{}'".format(table,
                                                                             data_type, 0)
        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def saveHuiYiUrlData(self, table, data, data_type, create_at):
        sha = data['sha']
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(data).replace('\'', '"'),
                'type': data_type,
                'create_at': create_at,
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info(sha)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class HuiYiLunWen_LunWenDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(HuiYiLunWen_LunWenDataDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getLunWenUrls(self, key, count, lockname):
        return self.redis_client.queue_spops(key=key, count=count, lockname=lockname)

    def saveRenWuToMysql(self, table, memo_list, create_at):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': create_at,
                }
                try:
                    self.mysql_client.insert_one(table=table, data=data)
                    self.logging.info('已保存人物队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('人物队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('人物队列数据已存在: {}'.format(sha))

    def saveJiGouToMysql(self, table, memo_list, create_at):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': create_at,
                }
                try:
                    self.mysql_client.insert_one(table=table, data=data)
                    self.logging.info('已保存机构队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('机构队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('机构队列数据已存在: {}'.format(sha))

    def deleteUrl(self, table, sha):
        sql = "delete from {} where `sha` = '{}'".format(table, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('论文任务已删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务删除异常: {}'.format(sha))

    def deleteLunWenUrl(self, table, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=table, data=data, where="sha = '{}'".format(sha))
            self.logging.info('论文任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务逻辑删除异常: {}'.format(sha))


class QiKanLunWen_QiKanTaskDao(storage.Dao):
    def saveData(self, table, sha, memo, create_at):
        new_memo = memo
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if data_status:
            old_memo = json.loads(data_status['memo'])
            old_column_name = old_memo['column_name']
            new_column_name = new_memo['column_name']
            if new_column_name not in old_column_name:
                new_memo['column_name'] = old_column_name + '|' + new_column_name
                # 存储数据
                data = {
                    'sha': sha,
                    'memo': str(new_memo).replace('\'', '"'),
                    'type': 'qikan',
                    'create_at': create_at,
                }
                self.mysql_client.update(table=table, data=data, where="`sha` = '{}'".format(sha))

        else:
            data = {
                'sha': sha,
                'memo': str(new_memo).replace('\'', '"'),
                'type': 'qikan',
                'create_at': create_at,
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))


class QiKanLunWen_LunWenTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(QiKanLunWen_LunWenTaskDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getQiKanTask(self, table, data_type):
        sql = "select * from {} where `type` = '{}' and `del` = '{}'".format(table,
                                                                             data_type, 0)
        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def saveLunWenUrlData(self, table, data, data_type, create_at):
        sha = data['sha']
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(data).replace('\'', '"'),
                'type': data_type,
                'create_at': create_at,
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info(sha)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class QiKanLunWen_LunWenDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(QiKanLunWen_LunWenDataDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getLunWenUrls(self, key, count, lockname):
        return self.redis_client.queue_spops(key=key, count=count, lockname=lockname)

    def saveRenWuToMysql(self, table, memo_list, create_at):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': create_at,
                }
                try:
                    self.mysql_client.insert_one(table=table, data=data)
                    self.logging.info('已保存人物队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('人物队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('人物队列数据已存在: {}'.format(sha))

    def saveJiGouToMysql(self, table, memo_list, create_at):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': create_at,
                }
                try:
                    self.mysql_client.insert_one(table=table, data=data)
                    self.logging.info('已保存机构队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('机构队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('机构队列数据已存在: {}'.format(sha))

    def deleteUrl(self, table, sha):
        sql = "delete from {} where `sha` = '{}'".format(table, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('论文任务已删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务删除异常: {}'.format(sha))




class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)

    def saveLunWenJiUrl(self, table, url_data, data_type, create_at):
        sha = hashlib.sha1(url_data['url'].encode('utf-8')).hexdigest()
        url = url_data['url']
        jibie = url_data['jibie']
        memo = {
            'sha': sha,
            'url': url,
            'jibie': jibie
        }
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(table, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': data_type,
                'create_at': create_at,
            }
            try:
                self.mysql_client.insert_one(table=table, data=data)
                self.logging.info('insert {}'.format(sha))
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))
