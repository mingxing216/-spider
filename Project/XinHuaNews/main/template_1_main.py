# -*-coding:utf-8-*-

'''

'''
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Project.XinHuaNews import config

if __name__ == '__main__':
    for data in config.COLUMN_INDEX_1:
        column_name = list(data.keys())[0]
        column_url = data[column_name]
        path = os.path.dirname(__file__) + os.sep + 'template_1.py'
        os.system('nohup python3 {} {} {} > /dev/null 2>&1 &'.format(path, column_name, column_url))
