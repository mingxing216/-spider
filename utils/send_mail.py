# -*- coding: utf-8 -*-
import smtplib
import sys
import os
from email.mime.text import MIMEText

sys.path.append(os.path.dirname(__file__) + os.sep + "../")

from log import log
from utils import timeutils

logger = log.ILog('Send_ERR_Email')


class Send_Mail(object):
    def __init__(self):
        self.email_user = 'king@jammyfm.com'  # 发送者账号
        self.email_pwd = 'Rockerfm520'  # 发送者密码
        self.maillist = ['464466847@qq.com']
        self.title = '测试邮件标题'
        self.content = '测试demo'

    def send_mail(self, username, passwd, recv, title, content, mail_host='smtp.exmail.qq.com', port=25):
        msg = MIMEText(content)  # 邮件内容
        msg['Subject'] = title  # 邮件主题
        msg['From'] = username  # 发送者账号
        msg['To'] = ','.join(recv)  # 接收者账号列表
        smtp = smtplib.SMTP(mail_host, port=port)  # 连接邮箱，传入邮箱地址，和端口号，smtp的端口号是25
        smtp.login(username, passwd)  # 发送者的邮箱账号，密码
        smtp.sendmail(username, recv, msg.as_string())
        # 参数分别是发送者，接收者，第三个是把上面的发送邮件的内容变成字符串
        smtp.quit()  # 发送完毕后退出smtp

        # print('email send success.')

    def run(self, title, content):
        i = 0
        for i in range(10):
            try:
                self.send_mail(self.email_user, self.email_pwd, self.maillist, title, content)
                logger.info("邮件发送成功")
                break
            # except SMTPDataError:
            #     logger.info("邮件发送失败")
            #     i += 1
            #     time.sleep(1)
            #     continue
            except Exception as e:
                pass

        if i == 10:
            logger.info("邮件发送失败次数达到10次")


if __name__ == '__main__':
    send = Send_Mail()
    send.run('weibo_spider_err', '这个是功能测试邮件, 无需关注～')
