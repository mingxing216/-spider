# -*-coding:utf-8-*-

'''

'''
import sys
import os
from multiprocessing import Pool as ProcessPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from ObjectBeas.CompanyTitle.middleware import download_middleware
from ObjectBeas.CompanyTitle.services import services
from ObjectBeas.CompanyTitle.dao import dao
from Utils import redispool_utils
from Utils import mysqlpool_utils

log_file_dir = 'CompanyTitle'  # LOG日志存放路径
LOGNAME = '<58同城企业名录爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.index_url = 'https://qy.58.com/citylist/'
        self.down = download_middleware.Download_58TongCheng()
        self.server = services.Service_58TongCheng()
        self.dao = dao.Dao_58TongCheng()

    def handle(self, add_url):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        # 获取地区页响应
        add_resp = self.down.getResp(logging=LOGGING, redis_client=redis_client, url=add_url)
        # 获取行业分类url
        industry_url_list = self.server.getIndustryUrlList(logging=LOGGING, resp=add_resp)
        for industry_url in industry_url_list:
            page = 1
            while 1:
                # 生成当前页url
                page_url = industry_url + 'pn{}'.format(page)
                # 获取当前页响应
                page_resp = self.down.getResp(logging=LOGGING, redis_client=redis_client, url=page_url)
                # 判断当前页是否有公司数据
                page_status = self.server.getPageStatus(logging=LOGGING, resp=page_resp)
                if page_status is False:
                    break
                # 获取当前页公司名称列表
                company_list = self.server.getCompantList(logging=LOGGING, resp=page_resp)
                # 存储公司名称
                self.dao.saveCompanyName(logging=LOGGING, mysql_client=mysql_client, data=company_list)
                page += 1

    def run(self):
        # 访问入口页， 获取响应
        index_resp = self.down.getIndexResp(logging=LOGGING, url=self.index_url)
        if index_resp is None:
            LOGGING.error('58同城首页响应获取失败')
            return
        # with open('index.html', 'w') as f:
        #     f.write(index_resp)
        # with open('index.html', 'r') as f:
        #     index_resp = f.read()
        # 提取地区分类url
        add_url_list = self.server.getAddUrlList(logging=LOGGING, resp=index_resp)
        process = ProcessPool(settings.COMPANY_TITLE_FOR_58TONGCHENG)
        # process = ProcessPool(1)
        for add_url in add_url_list:
            process.apply_async(func=self.handle, args=(add_url, ))
        process.close()
        process.join()




if __name__ == '__main__':
    main = SpiderMain()
    main.run()
