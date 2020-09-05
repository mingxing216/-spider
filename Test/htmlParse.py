#-*-coding:utf-8-*-

from bs4 import BeautifulSoup

text = '<p><strong>哈哈</strong><你好>呵呵<agodnsa></p>'

soup = BeautifulSoup(text, 'html5lib')
print(soup.prettify())

soup = BeautifulSoup(text, 'html.parser')
print(soup.prettify())

soup = BeautifulSoup(text, 'lxml')
print(soup.prettify())

