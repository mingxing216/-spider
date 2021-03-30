# -*- coding:utf-8 -*-

import re

content = '[1] nihao 我是'

print(re.findall(r"^\[\d+\](.*?)\[", content)[0])