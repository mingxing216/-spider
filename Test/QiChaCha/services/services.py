# -*-coding:utf-8-*-

'''

'''
import sys
import os
import re
from lxml import html

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

etree = html.etree

# 服务_基于登录
class Services_Logging(object):
    def __init__(self):
        pass

    # 获取地区分类url列表
    def getAddUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//ul[@class='sidebar-hangye-list']/li/a"):
            a_list = resp_etree.xpath("//ul[@class='sidebar-hangye-list']/li/a")
            for a in a_list:
                add_name = a.xpath("./text()")[0]
                add_url = 'https://www.qichacha.com' + a.xpath("./@href")[0] + '_1.html'
                logging.info('已获取地区分类url  {}: {}'.format(add_name, add_url))
                return_data.append(add_url)

            return return_data

        logging.error('获取地区分类url失败')
        return return_data

    # 获取行业分类url列表
    def getIndustryUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//div[@class='col-md-8 columns']/ul/li/a"):
            a_list = resp_etree.xpath("//div[@class='col-md-8 columns']/ul/li/a")
            for a in a_list:
                add_name = a.xpath("./text()")[0]
                # https://www.qichacha.com/gongsi_industry.shtml?industryCode=M&subIndustryCode=74&p=2
                industryCode = re.findall(r"_(.+)_", a.xpath("./@href")[0])[0]
                subIndustryCode = re.findall(r"_.+_(\d+)", a.xpath("./@href")[0])[0]
                add_url = 'https://www.qichacha.com/gongsi_industry.shtml?industryCode={}&subIndustryCode={}&p=1'.format(industryCode, subIndustryCode)
                logging.info('已获取地区分类url  {}: {}'.format(add_name, add_url))
                return_data.append(add_url)

            return return_data

        logging.error('获取行业分类url失败')
        return return_data

    # 获取企业url列表
    def getCompanyUrlList(self, logging, resp):
        return_data = []
        resp_etree = etree.HTML(resp)
        if resp_etree.xpath("//section[@id='searchlist']"):
            url_list = resp_etree.xpath("//section[@id='searchlist']/a/@href")
            for url in url_list:
                re_url = re.sub(r"_.*_", "_", url)
                save_url = 'https://www.qichacha.com' + re_url
                logging.info('已获取企业url: {}'.format(save_url))
                return_data.append(save_url)


            return return_data

        logging.error('获取企业url失败')
        return return_data

