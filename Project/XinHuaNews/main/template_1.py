# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import hashlib


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.XinHuaNews.middleware import download_middleware
from Project.XinHuaNews.service import service
from Project.XinHuaNews.dao import dao
from Project.XinHuaNews import config


class BastSpiderMain(object):
    def __init__(self, LOGGING):
        self.LOGGING = LOGGING
        self.download_middleware = download_middleware.Downloader(logging=self.LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.Server(logging=self.LOGGING)
        self.dao = dao.Dao(logging=self.LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self, LOGGING, column_name, column_url):
        super().__init__(LOGGING)
        self.column_name = column_name
        self.index = column_url
        self.url_list = []
        # self.url_list = [{'new_url': 'http://www.xinhuanet.com/2019-02/14/c_1124115719.htm', 'zhaiYao': '春节，是中国人阖家团聚的日子。对于中国科学院野外台站的科研人员来说，过节与平时并没什么两样，他们中的一部分人仍坚守在工作岗位。', 'faBuShiJian': '2019-02-11 08:50:07', 'title': '春节期间坚守一线的科研人员：无论如何数据不能断', 'biaoShi': 'http://www.xinhuanet.com/politics/titlepic/112409/1124097959_1549845915945_title0h.jpg'},]

    # 获取正文
    def getZhengWen(self, url):
        next_page_url = url
        return_data = []
        while 1:
            data = {}
            resp = self.download_middleware.getResp(url=next_page_url)
            # 获取正文
            zhengwen = self.server.getZhengWen(resp=resp)
            if zhengwen != '':
                # 获取组图
                img_url_data = self.server.getZuTu(resp=resp, url=next_page_url)
                # 下载图片
                for img_url in img_url_data:
                    # 保存图片到hbase
                    self.dao.saveMediaToMysql(url=img_url, type='image')

                if img_url_data:
                    # 替换正文中的图片url地址
                    zhengWen = self.server.tiHuanTuPian(zhengWen=zhengwen, img_url_list=img_url_data)
                    data['zhengWen'] = zhengWen
                else:
                    data['zhengWen'] = zhengwen

                return_data.append(data)

                # 获取下一页地址
                next_page_url = self.server.getNextPageUrl(resp=resp)
                if next_page_url is not None:
                    continue

                else:
                    return return_data

            else:
                return return_data

    # 获取正文
    def getZhengWen2(self, url):
        next_page_url = url
        return_data = []
        while 1:
            data = {}
            resp = self.download_middleware.getResp(url=next_page_url)
            # 获取正文
            zhengwen = self.server.getZhengWen2(resp=resp)
            if zhengwen != '':
                # 获取组图
                img_url_data = self.server.getZuTu2(resp=resp, url=next_page_url)
                # 下载图片
                for img_url in img_url_data:
                    # 保存图片到hbase
                    self.dao.saveMediaToMysql(url=img_url, type='image')

                if img_url_data:
                    # 替换正文中的图片url地址
                    zhengWen = self.server.tiHuanTuPian(zhengWen=zhengwen, img_url_list=img_url_data)
                    data['zhengWen'] = zhengWen
                else:
                    data['zhengWen'] = zhengwen

                return_data.append(data)

                # 获取下一页地址
                next_page_url = self.server.getNextPageUrl2(resp=resp)
                if next_page_url is not None:
                    continue

                else:
                    return return_data

            else:
                return return_data

    def start(self):
        # 获取时政页响应
        index_resp = self.download_middleware.getResp(url=self.index)
        if index_resp['status'] == 1:
            return

        # 获取来源nid
        nid = self.server.getNid(resp=index_resp)
        if nid is None:
            return
        # 生成新闻列表页首页API
        APIUrl = self.server.createApiUrl(nid=nid, page=1, count=12)
        # 获取响应
        APIUrlResp_1 = self.download_middleware.getResp(url=APIUrl)
        if APIUrlResp_1['status'] == 1:
            return

        # 获取总页数
        total = self.server.getTotal(resp=APIUrlResp_1, select_num=12)
        for page in range(total):
            # 生成新闻列表页API
            APIUrl = self.server.createApiUrl(nid=nid, page=page+1, count=12)
            # 获取响应
            APIUrlResp = self.download_middleware.getResp(url=APIUrl)
            if APIUrlResp['status'] == 1:
                continue

            # 获取新闻种子列表
            news_url_list = self.server.getNewsUrlList(resp=APIUrlResp)
            for news_url_data in news_url_list:
                self.url_list.append(news_url_data)

        for url_data in self.url_list:
            save_data = {}
            new_url = url_data['new_url']
            zhaiYao = url_data['zhaiYao']
            faBuShiJian = url_data['faBuShiJian']
            title = url_data['title']
            biaoShi = url_data['biaoShi']
            # 获取新闻页源码
            resp = self.download_middleware.getResp(url=new_url)
            if resp['status'] == 1:
                continue

            # 获取来源网站
            laiYuanWangZhan = self.server.getLaiYuanWangZhan(resp=resp)

            # 获取正文
            zhengWen = ''
            zhengWen_list = self.getZhengWen(url=new_url)
            if not zhengWen_list:
                # 换第二种方式获取
                zhengWen_list = self.getZhengWen2(url=new_url)
                if not zhengWen_list:
                    continue

                for data in zhengWen_list:
                    zhengWen += data['zhengWen']

            else:
                for data in zhengWen_list:
                    zhengWen += data['zhengWen']

            # 获取标签
            biaoQian = self.server.getBiaoQian(resp=resp)
            # 获取责任编辑
            zeRenBianJi = self.server.getZeRenBianJi(resp=resp)
            # 获取视频
            shiPin = self.server.getShiPin(resp=resp)
            # 保存视频到hbase
            if len(shiPin) > 10:
                self.dao.saveMediaToMysql(url=shiPin, type='video')
            # 获取发布者
            faBuZhe = ''
            # 获取编辑
            bianJi = ''
            # 获取设计
            sheJi = ''

            save_data['url'] = new_url
            save_data['zhaiYao'] = zhaiYao
            save_data['faBuShiJian'] = faBuShiJian
            save_data['title'] = title
            save_data['biaoQian'] = biaoQian
            save_data['biaoShi'] = biaoShi
            save_data['laiYuanWangZhan'] = laiYuanWangZhan
            save_data['zhengWen'] = zhengWen
            save_data['zeRenBianJi'] = zeRenBianJi
            save_data['shiPin'] = shiPin
            save_data['faBuZhe'] = faBuZhe
            save_data['bianJi'] = bianJi
            save_data['sheJi'] = sheJi
            save_data['key'] = new_url
            save_data['sha'] = hashlib.sha1(new_url.encode('utf-8')).hexdigest()
            save_data['ss'] = '资讯'
            save_data['ws'] = '新华网'
            save_data['clazz'] = '资讯_{}'.format(self.column_name)
            save_data['es'] = '{}'.format(self.column_name)
            save_data['biz'] = '文献大数据'
            save_data['ref'] = ''

            # 保存数据
            self.dao.saveDataToHbase(data=save_data)
            self.LOGGING.info('已完成: {}'.format(save_data['sha']))

            # break

# def process_start():
#     main = SpiderMain()
#     main.start()

def create_log(column_name):
    log_file_dir = 'XinHuaNews'  # LOG日志存放路径
    LOGNAME = '<新华网_{}>'.format(column_name)
    log.ILog(log_file_dir, LOGNAME)

if __name__ == '__main__':
    column_name = sys.argv[1]
    column_url = sys.argv[2]
    create_log(column_name)
    log_file_dir = 'XinHuaNews'  # LOG日志存放路径
    LOGNAME = '<新华网_{}>'.format(column_name)
    LOGGING = log.ILog(log_file_dir, LOGNAME)
    begin_time = time.time()
    main = SpiderMain(LOGGING, column_name, column_url)
    main.start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))

