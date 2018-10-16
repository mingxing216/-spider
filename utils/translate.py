# -*- coding: utf-8 -*-

'''
本文件负责翻译
需要翻译功能， 直接导入本文件， 对应调用功能函数即可
部分函数需要传参
'''

import requests
import re

# 检测语言url
testing_url = 'https://fanyi.baidu.com/langdetect'
# 翻译url
translate_url = 'https://fanyi.baidu.com/basetrans'

headers = {
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1"
}


def getLanguageType(content):
    '''
    检测输入内容的语种
    :param content: 你是我的小呀小苹果
    :return: {'error': 0, 'msg': 'success', 'lan': 'zh'}
    :error: {'error': -1, 'msg': 'length not ok'}
    '''
    data = {'query': content}
    resp = requests.post(url=testing_url, data=data, headers=headers).text

    return eval(resp)

def _translate(fromlanguage, tolanguage, content):
    '''
    翻译
    :param fromlanguage: 来源语种
    :param tolanguage: 目标语种
    :param content: 翻译内容
    :return: json
    '''
    data = {
        'from': fromlanguage,
        'to': tolanguage,
        'query': content,
    }
    resp = requests.post(url=translate_url, data=data, headers=headers).text

    return eval(resp)

def toEn(content):
    '''
    翻译成英文
    :param content: 要翻译的内容
    :return: 翻译成功的内容
    '''
    try:
        # 检测输入内容语种
        language_type = getLanguageType(content)['lan']
        if language_type == 'en':

            return content
        else:
            # 翻译成英文
            data = _translate(language_type, 'en', content)
            trans = ' '.join(re.findall(r'[\w,!.?]+', data['trans'][0]['dst']))
            trans = re.sub(',', '，', trans)

            return trans
    except Exception:

        return content

def toZh(content):
    '''
    翻译成中文
    :param content: 要翻译的内容
    :return: 翻译成功的内容
    '''
    try:
        # 检测输入内容语种
        language_type = getLanguageType(content)['lan']
        if language_type == 'zh':

            return content
        else:
            # 翻译成中文
            data = _translate(language_type, 'zh', content)
            trans = data['trans'][0]['dst']
            trans = re.sub(',', '，', trans)

            return trans
    except Exception:

        return content

