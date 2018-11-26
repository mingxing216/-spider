# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Utils import mysqlpool_utils


class Dao(object):
    def __init__(self, logging):
        self.logging = logging

    def demo(self, **kwargs):
        '''
        demo函数， 仅供参考
        '''
        mysql_client = kwargs['mysql_client']
        sha = kwargs['sha']
        sql = "select sha from ss_paper where `sha` = '%s'" % sha
        status = mysqlpool_utils.get_results(connection=mysql_client, sql=sql)
        if status:

            return False
        else:

            return True
