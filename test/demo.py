# -*-coding:utf-8-*-
import os
import sys
import re
import requests
import hashlib
import pprint
import redis
import threading
import random
import time
from redis import StrictRedis
from urllib.parse import urlparse
from multiprocessing import Pool

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings

from utils import redis_dbutils

# def inputdata():
#     for i in range(1000):
#         redis_dbutils.saveSet('comlieted', i)
#
# inputdata()

# def demo():
#     while True:
#         a = redis_dbutils.spop(key='comlieted', lockname='spop_demo')
#         if a:
#             print(a)
#         else:
#             break
#
# po = Pool(4)
# for i in range(4):
#     po.apply_async(func=demo)
#
# po.close()
# po.join()


bs = b'\xef\xbb\xbf<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n  <head>\r\n    <META http-equiv="Content-Type" content="text/html; charset=utf-8">\r\n    <link rel="stylesheet" type="text/css" href="http://piccache.cnki.net/kdn/KCMS/detail/resource/gb/css_min/Global.min.css?v=FBC16D09D6F9935E">\r\n    <link rel="stylesheet" type="text/css" href="http://piccache.cnki.net/kdn/KCMS/detail/resource/gb/css_min/ecplogin.min.css?v=FBC16D09D6F9935E"><script type="text/javascript" src="/kcms/detail/js/getLink.aspx"></script><script type="text/javascript" src="http://piccache.cnki.net/kdn/KCMS/detail/js/jquery-1.4.2.min.js"></script><script type="text/javascript" src="http://piccache.cnki.net/kdn/KCMS/detail/resource/gb/js/min/rs.min.js?v=FBC16D09D6F9935E"></script><script type="text/javascript" src="http://piccache.cnki.net/kdn/KCMS/detail/js/min/Common.min.js?v=FBC16D09D6F9935E0129"></script><script type="text/javascript" src="http://piccache.cnki.net/kdn/KCMS/detail/js/min/refer.min.js?v=FBC16D09D6F9935E"></script></head>\r\n  <body onload="ResezeParent(10);SetParentCatalog();"><script type="text/javascript" src="http://piccache.cnki.net/kdn/KCMS/detail/js/min/WideScreen.min.js"></script><h2 id="catalog_CkFiles" class="title1">\r\n      \xe5\x8f\x82\xe8\x80\x83\xe6\x96\x87\xe7\x8c\xae\r\n      <span class="desc">\xef\xbc\x88\xe5\x8f\x8d\xe6\x98\xa0\xe6\x9c\xac\xe6\x96\x87\xe7\xa0\x94\xe7\xa9\xb6\xe5\xb7\xa5\xe4\xbd\x9c\xe7\x9a\x84\xe8\x83\x8c\xe6\x99\xaf\xe5\x92\x8c\xe4\xbe\x9d\xe6\x8d\xae\xef\xbc\x89</span></h2>\r\n    <div class="essayBox">\r\n      <div class="dbTitle">\xe5\x9b\xbd\xe9\x99\x85\xe6\x9c\x9f\xe5\x88\x8a\xe6\x95\xb0\xe6\x8d\xae\xe5\xba\x93<b class="titleTotle">\r\n          \xe5\x85\xb1<span name="pcount" id="pc_SSJD">7</span>\xe6\x9d\xa1\r\n        </b></div>\r\n      <ul class="&#xA;            ebBd&#xA;          ">\r\n        <li class=""><em>[1]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SJEH15062500006308&amp;dbcode=SJEH">Construction of multi-soliton solutions for the $L^2$-supercritical gKdV and NLS equations</a>[J] .   \r\n    Rapha?l C?te,Yvan Martel,Frank Merle.&nbsp&nbspRevista Matem\xc3\xa1tica Iberoamericana .      \r\n    2011\r\n      (1)\r\n    </li>\r\n        <li class="&#xA;          double&#xA;        "><em>[2]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SJES13011601360730&amp;dbcode=SJES">High-speed excited multi-solitons in nonlinear Schr?dinger equations</a>[J] .   \r\n    &nbsp&nbspJournal de math\xc3\xa9matiques pures et appliqu\xc3\xa9es .      \r\n    2011\r\n      (2)\r\n    </li>\r\n        <li class=""><em>[3]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SSJD15103100107676&amp;dbcode=SSJD">Sharp Threshold of Global Existence and Instability of Standing Wave for a Davey-Stewartson System</a>[J] .   \r\n    Zaihui Gan,Jian Zhang.&nbsp&nbspCommunications in Mathematical Physics .      \r\n    2008\r\n      (1)\r\n    </li>\r\n        <li class="&#xA;          double&#xA;        "><em>[4]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SJES13012201149738&amp;dbcode=SJES">Multi solitary waves for nonlinear Schr?dinger equations</a>[J] .   \r\n    Yvan Martel,Frank Merle.&nbsp&nbspAnnales de l\xe2\x80\x99Institut Henri Poincare / Analyse non lineaire .      \r\n    2006\r\n      (6)\r\n    </li>\r\n        <li class=""><em>[5]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SSJD00000031792&amp;dbcode=SSJD">On the initial value problem and scattering of solutions for the generalized Davey-Stewartson systems</a>[J] .   \r\n    Baoxiang Wang,Boling Guo.&nbsp&nbspScience in China Series A: Mathematics .      \r\n    2001\r\n      (8)\r\n    </li>\r\n        <li class="&#xA;          double&#xA;        "><em>[6]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=SSJD00002849849&amp;dbcode=SSJD">Stability of standing waves for the generalized Davey-Stewartson system</a>[J] .   \r\n    Masahito Ohta.&nbsp&nbspJournal of Dynamics and Differential Equations .      \r\n    1994\r\n      (2)\r\n    </li>\r\n        <li class=""><em>[7]</em><a target="kcmstarget" href="/kcms/detail/detail.aspx?filename=STJD778339854&amp;dbcode=STJD">On the existence of standing waves for a davey-stewartson system</a>[J] .   \r\n    Rolci  Cipolatti.&nbsp&nbspCommunications in Partial Differential Equations .      \r\n    1992\r\n      (5-6)\r\n    </li>\r\n      </ul>\r\n    </div>\r\n    <div class="essayBox">\r\n      <div class="dbTitle">\xe5\xa4\x96\xe6\x96\x87\xe9\xa2\x98\xe5\xbd\x95\xe6\x95\xb0\xe6\x8d\xae\xe5\xba\x93<b class="titleTotle">\r\n          \xe5\x85\xb1<span name="pcount" id="pc_CRLDENG">21</span>\xe6\x9d\xa1\r\n        </b></div>\r\n      <ul class="&#xA;            ebBd&#xA;          ">\r\n        <li class=""><em>\r\n          [21]\r\n        </em><a onclick="&#xA;              OpenCRLDENG(\'Multi-speed solitary wave solutions for a coherently coupled nonlinear Schr\xc2\xa8odinger system\');&#xA;            ">Multi-speed solitary wave solutions for a coherently coupled nonlinear Schr\xc2\xa8odinger system</a>.\r\n         Wang Z,Cui S B. Journal of Mathematical Physics\r\n        . 2015</li>\r\n      </ul>\r\n      <div class="pageBar"><span id="CRLDENG"></span><script type="text/javascript">\n          nEnable=1;\n          ShowPage(\'21\',\'CRLDENG\',\'Mark\');\n        </script></div>\r\n    </div>\r\n  </body>\r\n</html>'

print(bs.decode())