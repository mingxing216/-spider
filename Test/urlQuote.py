#-*-coding:utf-8-*-
import re
from urllib import parse
from urllib import request

url  = 'http://WWW.TEXT.com:80/hello%3a/bar+a'

def up(matched):
    intStr = matched.group("%")
    print(intStr)

url_d = re.sub(r"%.{2}", up, re.sub(r":\d+" ,"", url))

url_1 = parse.quote(url_d.lower())

print(url_1)
