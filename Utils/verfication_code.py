# -*- coding:utf-8 -*-
import base64
import json
from io import BytesIO
from sys import version_info
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout
from requests.exceptions import ReadTimeout
from PIL import Image

from Utils import timers


class VerificationCode(object):
    def __init__(self, _uname, _passwd, logger, debug=False):
        self.user_name = _uname
        self.password = _passwd
        self.DEBUG = debug
        self.logger = logger
        self.timer = timers.Timer()

    def get_image_obj(self, img_content):
        self.logger.info('captcha | 获取图片对象')
        file = BytesIO(img_content)
        image_obj = Image.open(file)
        if self.DEBUG:
            image_obj.show()
        return image_obj

    def get_code_from_img_content(self, img_content):
        self.timer.start()
        self.logger.info('captcha start | 处理验证码')
        return self.get_code_from_image_obj(self.get_image_obj(img_content))

    def get_code_from_image_obj(self, image_obj):
        self.logger.info('captcha | 获取验证码')
        img = image_obj.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        if version_info.major >= 3:
            b64 = str(base64.b64encode(buffered.getvalue()), encoding='utf-8')
        else:
            b64 = str(base64.b64encode(buffered.getvalue()))
        data = {'username': self.user_name, 'password': self.password, 'image': b64,
                'typeid': 7, 'remark': '请区分大小写输入字符'}
        for _i in range(5):
            try:
                result = json.loads(requests.post("http://api.ttshitu.com/base64", json=data, timeout=30).text)
                # print(result)
                if result['success']:
                    self.logger.info('captcha end | 验证码获取成功 | use time: {}'.format(self.timer.use_time()))
                    return result["data"]
                else:
                    self.logger.error(
                        'captcha end | 验证码获取失败, {} | use time: {}'.format(result["message"], self.timer.use_time()))
                    self.report_error(result["data"]["id"])
                    return

            except (ConnectTimeout, ReadTimeout) as e:
                self.logger.error('captcha | 验证码获取失败, {}'.format(e))
                continue

            except ConnectionError as e:
                self.logger.error('captcha | 验证码获取失败, {}'.format(e))
                continue

            except Exception as e:
                self.logger.error('captcha | 验证码获取失败, {}'.format(e))
                continue
        else:
            self.logger.error('captcha | 验证码获取失败 | use time: {}'.format(self.timer.use_time()))

    @staticmethod
    def report_error(id_num):
        data = {"id": id_num}
        result = json.loads(requests.post("http://api.ttshitu.com/reporterror.json", json=data, timeout=30).text)
        # print(result)
        if result['success']:
            return "报错成功"
        else:
            return result["message"]
