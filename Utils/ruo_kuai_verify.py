# -*- coding: cp936 -*-
import sys
import os
import requests
from hashlib import md5


sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings


class RClient(object):

    def __init__(self):
        self.username = settings.r_username
        self.password = md5(settings.r_password.encode('utf8')).hexdigest()
        self.soft_id = settings.r_soft_id
        self.soft_key = settings.r_soft_key
        self.base_params = {
            'username': self.username,
            'password': self.password,
            'softid': self.soft_id,
            'softkey': self.soft_key,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }

    def rk_create(self, im, im_type, timeout=60):
        params = {
            'typeid': im_type,
            'timeout': timeout,
        }
        params.update(self.base_params)
        files = {'image': ('a.jpg', im)}
        r = requests.post('http://api.ruokuai.com/create.json', data=params, files=files, headers=self.headers)
        return r.json()

    def rk_report_error(self, im_id):
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://api.ruokuai.com/reporterror.json', data=params, headers=self.headers)
        return r.json()


if __name__ == '__main__':
    rc = RClient()
    # im = open('/home/master/Project/SpiderFrame/Test/DaWeiSpiderProject/service/../../../Static/Img/register_verify.png', 'rb').read()
    # r = rc.rk_create(im, 3000)
    # print(r)
    # print(r['Result'])
    with open('/home/master/Project/SpiderFrame/Test/DaWeiSpiderProject/service/../../../Static/Img/register_verify.png', 'rb') as f:
        im = f.read()
    r = rc.rk_create(im, 3000)
    print(r)
    print(r['Result'])