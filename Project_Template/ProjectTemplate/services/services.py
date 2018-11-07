# -*-coding:utf-8-*-

'''

'''
import sys
import os
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree

class Services(object):
    def __init__(self):
        pass


    def demo(self, **kwargs):
        '''
        html处理 【demo函数， 仅供参考】
        '''
        html = kwargs['html']
        resp = bytes(bytearray(html, encoding='utf-8'))
        html_etree = etree.HTML(resp)
        title = html_etree.xpath("//p[@class='title']/a/text()")
        if title:

            return title[0]
        else:

            return ""
