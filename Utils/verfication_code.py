#-*-coding:utf-8-*-
import base64
import json
from io import BytesIO
from sys import version_info
import requests
from PIL import Image


class VerificationCode:
    def __init__(self, session, _uname, _passwd, headers=None, proxies=None, debug=False):
        self.user_name = _uname
        self.password = _passwd
        self.s = session
        self.headers = headers
        self.proxies = proxies
        self.DEBUG = debug

    def get_image_obj(self, img_url):
        print('请求验证码图片')
        file = BytesIO(self.s.get(url=img_url, headers=self.headers, proxies=self.proxies, timeout=10).content)
        image_obj = Image.open(file)
        if self.DEBUG:
            image_obj.show()
        return image_obj

    def get_code_by_image_url(self, image_url):
        return self.get_code_from_image_obj(self.get_image_obj(image_url))

    def get_code_from_image_obj(self, image_obj):
        print('获取验证码')
        img = image_obj.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        if version_info.major >= 3:
            b64 = str(base64.b64encode(buffered.getvalue()), encoding='utf-8')
        else:
            b64 = str(base64.b64encode(buffered.getvalue()))
        data = {"username": self.user_name, "password": self.password, "image": b64}
        result = json.loads(requests.post("http://api.ttshitu.com/base64", json=data, timeout=10).text)
        print(result)
        if result['success']:
            return {'result': True, 'data': result["data"]}
        else:
            self.reportError(result["data"]["id"])
            return {'result': False, 'message': result["message"]}

    def reportError(self, id):
        data = {"id": id}
        result = json.loads(requests.post("http://api.ttshitu.com/reporterror.json", json=data).text)
        print(result)
        if result['success']:
            return "报错成功"
        else:
            return result["message"]

