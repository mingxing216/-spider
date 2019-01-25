# -*-coding:utf-8-*-
'''
自动注册佰腾账号
'''
import os
import sys
import time
from selenium.webdriver.support.select import Select
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Utils import user_agent_u
from Utils import redispool_utils
from Utils import mysqlpool_utils
from Project.DaWeiSpiderProject.services import services
from Project.DaWeiSpiderProject.dao import dao

log_file_dir = 'DaWeiSpiderProject'  # LOG日志存放路径
LOGNAME = '<大为专利账号注册>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class RegisterBaiTeng(object):
    def __init__(self):
        self.register_url = 'http://www.innojoy.com/account/register.html'
        self.server = services.Services(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)
        self.OrangeAPI_uid = settings.OrangeAPI_uid # 橙子API账号
        self.OrangeAPI_pwd = settings.OrangeAPI_pwd # 橙子API密码
        self.Orange_Pid = settings.Orange_Pid
        self.random_str = ("圣诚杰安博彬宝斌超盛畅灿纯恩帆福富贵桂瀚豪翰皓弘恒海宏洪涵慧荷蕙航嘉俊君峻健和禾佳静娇娟净睛善康"
     "坤兰岚莲丽立亮伶俪明名铭美宁朋鹏琪芹清晴胜思顺舒森升潭婷伟文益宜韵阳运乐怡芸盈园翊智哲志振展忠昭真正雅悦莹娅欣勋轩旭新熙金真")

    def registerBaiTeng(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        while True:
            # 登录橙子API, 获取登录成功返回参数
            landing_data = self.server.landingAPI(uid=self.OrangeAPI_uid, pwd=self.OrangeAPI_pwd)
            Orange_Uid = landing_data['Uid']
            Orange_Token = landing_data['Token']
            Orange_Balance = landing_data['Balance'] # 橙子账号余额

            if Orange_Balance == 0:
                LOGGING.error('橙子API余额不足0元')
                time.sleep(10)
                continue

            # 随机生成User-Agent
            ua = user_agent_u.get_ua()
            # 获取短效代理IP
            proxy = self.server.getProxy(redis_client=redis_client, logging=LOGGING)

            # 创建driver
            register_driver = self.server.creatDriver(proxy=proxy, ua=ua)

            # 访问注册页
            try:
                register_driver.get(self.register_url)
            except:
                LOGGING.info('访问超时')
                register_driver.quit()
                continue

            # 判断注册页面是否加载完成
            status = self.server.judgeHtmlComplete(driver=register_driver, xpath="//img[@id='idChkImage']")
            if status is False:
                LOGGING.info('页面加载失败')
                register_driver.quit()
                continue

            # 获取一个橙子手机号
            mobile = self.server.getPhoneNumber(uid=Orange_Uid, pid=self.Orange_Pid, token=Orange_Token)
            if mobile == '余额不足，请充值':
                LOGGING.info('橙子余额不足，请充值')
                register_driver.quit()
                continue
            # 输入手机号
            register_driver.find_element_by_id('idMobilePhone').click()
            register_driver.find_element_by_id('idMobilePhone').send_keys(mobile)
            # 点击发送短信验证码
            register_driver.find_element_by_id('getcheckcode').click()
            # 输入邮箱
            register_driver.find_element_by_id('idEMail').click()
            register_driver.find_element_by_id('idEMail').send_keys(mobile + '@163.com')
            # 输入昵称
            register_driver.find_element_by_id('idName').click()
            register_driver.find_element_by_id('idName').send_keys(''.join(random.sample(self.random_str, random.randint(5, 12))))
            # 输入密码
            register_driver.find_element_by_id('idPassword').click()
            register_driver.find_element_by_id('idPassword').send_keys(mobile)
            # 第二次输入密码
            register_driver.find_element_by_id('idPassword2').click()
            register_driver.find_element_by_id('idPassword2').send_keys(mobile)
            # 输入公司名称
            register_driver.find_element_by_id('idCompany').click()
            register_driver.find_element_by_id('idCompany').send_keys(''.join(random.sample(self.random_str, random.randint(5, 12))))
            # 输入职位
            register_driver.find_element_by_id('idPosition').click()
            register_driver.find_element_by_id('idPosition').send_keys(''.join(random.sample(self.random_str, random.randint(5, 12))))
            # 选择职业
            s1 = Select(register_driver.find_element_by_id('idProfession'))
            s1.select_by_index(2)
            # 选择行业
            s2 = Select(register_driver.find_element_by_id('idIndustry'))
            s2.select_by_index(2)
            # 获取手机短信验证码
            mobile_verify_code = self.server.getMobileVerifyCode(uid=Orange_Uid, pid=self.Orange_Pid, mobile=mobile,
                                                                 token=Orange_Token)
            if mobile_verify_code is None:
                LOGGING.info('获取手机短信验证码为空')
                register_driver.quit()
                continue
            # 输入手机短信验证码
            register_driver.find_element_by_id('sms_code').click()
            register_driver.find_element_by_id('sms_code').send_keys(mobile_verify_code)
            # 获取并输入验证码
            img = self.server.get_or_input_img_verify(driver=register_driver)
            # 点击注册
            register_driver.find_element_by_id('idSubmit').click()
            time.sleep(3)
            # 判断是否注册成功
            register_ststus = register_driver.find_element_by_id('dialog-message-span').text

            if register_ststus == ' 验证码信息输入有误！ ' or register_ststus == ' 验证码已失效。 ':
                LOGGING.info('图片验证码错误')
                # 点击换验证码
                register_driver.find_element_by_id('btn_Next').click()
                time.sleep(0.3)
                # 获取并输入验证码
                img = self.server.get_or_input_img_verify(driver=register_driver)

            if register_ststus != '注册成功！':
                LOGGING.info(register_ststus)
                # 释放手机号
                self.server.cancelSMSRecv(uid=Orange_Uid, pid=self.Orange_Pid, mobile=mobile,
                                                   token=Orange_Token)
                register_driver.quit()
                # 删除图片验证码
                os.remove(img)
                time.sleep(5)
                continue

            # 释放手机号
            self.server.cancelSMSRecv(uid=Orange_Uid, pid=self.Orange_Pid, mobile=mobile, token=Orange_Token)

            register_driver.quit()

            # 删除图片验证码
            os.remove(img)

            # 保存账号
            self.dao.saveInnojoyMobile(mysql_cli=mysql_client, data=mobile)
            LOGGING.info('账号保存成功')

            # return mobile


if __name__ == '__main__':
    main = RegisterBaiTeng()
    main.registerBaiTeng()