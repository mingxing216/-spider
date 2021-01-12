# -*- coding:utf-8 -*-

"""
识别图片上的验证码
"""

import base64
from PIL import Image
from io import BytesIO
import platform
import pytesseract
import re
from PIL import ImageFile

from Utils import timers

ImageFile.LOAD_TRUNCATED_IMAGES = True


class RecognizeCode(object):
    def __init__(self, logger):
        self.total = 0
        self.succ_count = 0
        self.failed_count = 0
        self.logger = logger
        self.timer = timers.Timer()

    def image_stream(self, image_stream, show=False, length=4, invalid_charset='', need_pretreat=True, lang='num'):
        return self.image_obj(Image.open(image_stream), show, length, invalid_charset, need_pretreat, lang)

    def image_file(self, file_name, show=False, length=4, invalid_charset='', need_pretreat=True, lang='num'):
        with open(file_name, 'rb') as file:
            return self.image_stream(file, show, length, invalid_charset, need_pretreat, lang)

    def image_data(self, image_data, show=False, length=4, invalid_charset='', need_pretreat=True, lang='num'):
        self.logger.info('captcha start | 开始处理验证码')
        self.timer.start()
        return self.image_stream(BytesIO(image_data), show, length, invalid_charset, need_pretreat, lang)

    def image_obj(self, image, show=False, length=4, invalid_charset='', need_pretreat=True, lang='num'):
        if show:
            image.show()
        if need_pretreat:
            image_grey = image.convert('L')
            # 转为灰度图片
            # image_grey.show()
            # 二值化
            table = []
            for i in range(256):
                if i < 140:
                    table.append(0)
                else:
                    table.append(1)
            image_bi = image_grey.point(table, '1')
        else:
            image_bi = image
        # 识别验证码
        os_system = platform.system()

        # Should added tesseract into environment variable PATH
        if os_system == 'Windows':
            pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        elif os_system == 'Linux':
            pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
        elif os_system == 'Darwin':
            pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
        else:
            raise EnvironmentError("Unsupported platform {}".format(os_system))
        verify_code = pytesseract.image_to_string(image_bi, lang=lang, config='--psm 7')

        if invalid_charset:
            cop = re.compile("[{}]".format(invalid_charset))  # 匹配的其他字符
            verify_code = cop.sub('', verify_code)  # 将string1中匹配到的字符替换成空字符
        if length:
            verify_code = verify_code[0:length]

        self.logger.info('captcha end | 结束处理验证码 | use time: {}'.format(self.timer.use_time()))

        return verify_code

    # status: successed True; failed False
    # 统计成功错误比率；
    # 积累错误案例，作为训练集
    def report(self, image, code, status):
        self.total += 1
        if status:
            self.succ_count += 1
        else:
            self.failed_count += 1
            if self.logger:
                self.logger.info("captcha | RecognizeCode: {} {}".format(code, base64.b64encode(image)))

    def show_report(self):
        return "captcha | Total:{} Succ:{} Failed:{}".format(self.total, self.succ_count, self.failed_count)
