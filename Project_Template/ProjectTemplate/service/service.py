# -*-coding:utf-8-*-

'''

'''
import sys
import os
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class Server(object):
    def __init__(self, logging):
        self.logging = logging

    def getTitle(self, resp):
        '''This is demo'''
        selector = Selector(text=resp)
        title = selector.xpath("//title/text()").extract_first()

        return title






