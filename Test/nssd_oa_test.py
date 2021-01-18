# -*- coding:utf-8 -*-
import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import requests
from scrapy import Selector

from Log import logging
from Utils import user_agent_u, proxy_pool
from Utils.captcha import RecognizeCode

LOG_FILE_DIR = 'Test'  # LOG日志存放路径
LOG_NAME = 'nssd_oa_data'  # LOG名
logger = logging.Logger(LOG_FILE_DIR, LOG_NAME)


class CaptchaProcessor(object):
    def __init__(self):
        self.session = requests.Session()
        self.headers = {'User-Agent': user_agent_u.get_ua()}
        self.proxy_obj = proxy_pool.ProxyUtils(logger=logger)
        self.recognize_code = RecognizeCode(logger)

    def downloader(self, method, url, data=None):
        # adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        self.session.keep_alive = False  # 关闭多余连接

        headers = {'User-Agent': user_agent_u.get_ua()}
        ip = self.proxy_obj.get_proxy()
        proxies = {'http': 'http://' + ip,
                   'https': 'https://' + ip}

        try:
            if method == 'GET':
                logger.info('downloader | GET 请求')
                r = self.session.get(url=url, headers=headers, params=data, proxies=proxies, timeout=(5, 10))

            elif method == 'POST':
                logger.info('downloader | POST 请求')
                r = self.session.post(url=url, headers=headers, data=data, proxies=proxies, timeout=(5, 10))

            else:
                logger.error('downloader | 其它请求不支持')
                return

        except Exception as e:
            logger.error('downloader | 请求失败: {}'.format(e))
            return

        logger.info('downloader | 请求成功')
        return r

    # 获取验证码参数
    def get_captcha(self, text):
        captcha_data = {}
        selector = Selector(text=text)
        try:
            captcha_data['__VIEWSTATE'] = selector.xpath("//input[@id='__VIEWSTATE']/@value").extract_first()
            captcha_data['__EVENTVALIDATION'] = selector.xpath(
                "//*[@id='__EVENTVALIDATION']/@value").extract_first()
            captcha_data['btnOk'] = selector.xpath("//*[@id='btnOk']/@value").extract_first()

        except Exception:
            return captcha_data

        return captcha_data

    # 获取图片url
    def get_img_url(self, text):
        selector = Selector(text=text)
        try:
            img_url = 'http://103.247.176.188/' + selector.xpath("//img[@id='imgCode1']/@src").extract_first()

        except Exception:
            return ''

        return img_url

    def is_captcha_page(self, resp):
        logger.info('process | 判断是否有验证码')
        if len(resp.content) > 2048:
            return False
        if '验证码' in resp.text:
            return True
        return False

    def get_resp(self, url, method):
        retry_count = 10
        logger.info('process start | 首次请求 | url: {}'.format(url))
        resp = self.downloader(url=url, method=method)
        if resp is None:
            return

        logger.info('process | 首次请求完成 | url: {}'.format(url))
        captcha_page = self.is_captcha_page(resp)

        for i in range(retry_count):
            if captcha_page:
                try:
                    logger.info('process | 出现验证码')
                    # 获取验证码及相关参数
                    form_data = self.get_captcha(resp.text)
                    image_url = self.get_img_url(resp.text)
                    logger.info('process | 请求验证码图片 | url: {}'.format(image_url))
                    img_content = self.downloader(url=image_url, method='GET').content
                    # data_dict = self.verfication_code.get_code_from_img_content(img_content)
                    # code = data_dict['result']
                    logger.info('process | 识别验证码')
                    code = self.recognize_code.image_data(img_content, show=False, length=4,
                                                          invalid_charset="^0-9^A-Z^a-z")
                    form_data['iCode'] = code
                    logger.info('process | 一次验证码处理完成')
                    # 带验证码访问
                    real_url = resp.url
                    logger.info('process | post请求页面 | url: {}'.format(real_url))
                    resp = self.downloader(url=real_url, method='POST', data=form_data)
                    if resp is None:
                        return
                    # 判断是否还有验证码
                    captcha_page = self.is_captcha_page(resp)
                    # if captcha_page:
                    #     self.logger.info('captcha | 验证码错误')
                        # self.verfication_code.report_error(data_dict['id'])
                    self.recognize_code.report(img_content, code, not captcha_page)
                    logger.info(
                        'process | 一次请求完成时间 | url: {}'.format(resp.url))

                except Exception:
                    logger.error('process end | 请求错误 | url: {}'.format(resp.url))
                    return

            else:
                logger.info(
                    'process end | 请求成功 | url: {} | count: {}'.format(resp.url, i))
                return resp

        logger.error(
            'process end | 验证码识别失败 | url: {} | count: {}'.format(resp.url, retry_count))
        return


    def run(self):
        while True:
            profile_resp = self.get_resp(url='http://103.247.176.188/View.aspx?id=206139023', method='GET')
            logger.info('profile_resp: {}'.format(profile_resp))

            fulltext_resp = self.get_resp(url='http://103.247.176.188/Direct.aspx?dwn=1&id=206139023', method='GET')
            logger.info('fulltext_resp: {}'.format(fulltext_resp))


def start():
    test = CaptchaProcessor()
    test.run()


def process_start():
    # 创建线程池
    tpool = ThreadPoolExecutor(max_workers=32)
    for i in range(32):
        tpool.submit(start)
    tpool.shutdown(wait=True)


if __name__ == '__main__':
    # 创建进程池
    ppool = ProcessPoolExecutor(max_workers=4)
    for i in range(4):
        ppool.submit(process_start)
    ppool.shutdown(wait=True)
