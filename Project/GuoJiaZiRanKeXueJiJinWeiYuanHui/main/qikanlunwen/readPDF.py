#-*-coding:utf-8-*-

import requests
import re
from urllib.request import urlopen
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed

def readPDF(url):
    # # 以二进制形式打开pdf文件
    # with open(path, "rb") as f:

    # 访问文档url，获取响应
    # f = requests.get(url).text
    f = urlopen(url)
    # 创建一个pdf文档分析器
    parser = PDFParser(f)
    # 创建pdf文档
    pdfFile = PDFDocument()
    # 链接分析器与文档对象
    parser.set_document(pdfFile)
    pdfFile.set_parser(parser)
    # 提供初始化密码
    pdfFile.initialize()
    # 检测文档是否提供txt转换
    if not pdfFile.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        # 解析数据
        # 数据管理
        manager = PDFResourceManager()
        # 创建一个PDF设备对象
        laparams = LAParams()
        device = PDFPageAggregator(manager, laparams=laparams)
        # 解释器对象
        interpreter = PDFPageInterpreter(manager, device)

        # 开始循环处理，每次处理一页
        for page in pdfFile.get_pages():
            # 使用页面解释器读取页面
            interpreter.process_page(page)
            # 使用聚合器读取页面页面内容
            layout = device.get_result()
            for x in layout:
                # if(isinstance(x, LTTextBoxHorizontal)):
                if hasattr(x, 'get_text'):
                    with open('pdf.txt', "a") as f:
                        str = x.get_text()
                        # print(str)
                        f.write(str+"\n")

readPDF('http://ir.nsfc.gov.cn/paperDownload/1000015339376.pdf')