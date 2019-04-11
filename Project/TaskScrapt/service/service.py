# -*-coding:utf-8-*-

'''

'''
import sys
import os
import pypinyin
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


class Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getCateidPinyin(self, cateid):
        cateid_pinyin = ''
        for i in pypinyin.pinyin(cateid, style=pypinyin.NORMAL):
            cateid_pinyin += ''.join(i)

        return cateid_pinyin






