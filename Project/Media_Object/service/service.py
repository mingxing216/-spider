# -*-coding:utf-8-*-

'''

'''
import sys
import os
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree


def error(func):
    def wrapper(self, *args, **kwargs):
        if args[0]:
            data = func(self, *args, **kwargs)
            return data
        else:
            return None

    return wrapper


class Server(object):
    def __init__(self, logging):
        self.logging = logging

    @error
    def getTitle(self, resp):
        '''This is demo'''
        response = resp.content.decode('utf-8')
        response_etree = etree.HTML(response)
        title = response_etree.xpath("//title/text()")[0]

        return title






