# -*-coding:utf-8-*-

'''

'''
import sys
import os


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Test.XinHuaNews.middleware import download_middleware
from Test.XinHuaNews.services import services

log_file_dir = 'XinHuaNews'  # LOG日志存放路径
LOGNAME = '<新华新闻爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Download_Middleware(logging=LOGGING)
        self.server = services.Services(logging=LOGGING)
        self.index_url = 'http://m.xinhuanet.com/'

    # 抓取模板1
    def newsTemplate_1(self, redis_client, url, news_from_title):
        # 获取来源页html
        resp = self.download.getResponse(redis_client=redis_client, url=url)
        # 获取来源nid
        nid = self.server.getNewsFromNid(resp=resp)
        if nid is None:
            return
        # 生成新闻列表页首页API
        APIUrl = self.server.createApiUrl(nid=nid, page=1, count=12)
        # 获取首页API响应
        APIUrlResp_1 = self.download.getResponse(redis_client=redis_client, url=APIUrl)
        # 获取总页数
        page_sum = self.server.getPageSum(resp=APIUrlResp_1, select_num=12)
        for page in range(page_sum):
            # 生成新闻列表页API
            APIUrl = self.server.createApiUrl(nid=nid, page=page + 1, count=12)
            # 获取首页API响应
            APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
            # 获取新闻种子列表
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, news_from_title=news_from_title)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open('url_data.txt', 'a') as f:
                    f.write(str(NewUrl) + '\n')

    # 抓取模板2
    def newsTemplate_2(self, redis_client, url, news_from_title):
        jsAPI = 'http://www.xinhuanet.com/video/xinhuaradio/ej2018/scripts/home_mob.js'
        # 获取JS接口响应
        jsResp = self.download.getResponse(redis_client=redis_client, url=jsAPI)
        # 获取colNid
        colNid = self.server.getColNid(resp=jsResp)
        if colNid is None:
            return
        # 生成新闻列表页首页API
        APIUrl = self.server.createApiUrl(nid=colNid, page=1, count=12)
        # 获取首页API响应
        APIUrlResp_1 = self.download.getResponse(redis_client=redis_client, url=APIUrl)
        # 获取总页数
        page_sum = self.server.getPageSum(resp=APIUrlResp_1, select_num=12)
        for page in range(page_sum):
            # 生成新闻列表页API
            APIUrl = self.server.createApiUrl(nid=colNid, page=page + 1, count=12)
            # 获取首页API响应
            APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
            # 获取新闻种子列表
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, news_from_title=news_from_title)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open('url_data.txt', 'a') as f:
                    f.write(str(NewUrl) + '\n')

    # 抓取模板3
    def newsTemplate_3(self, redis_client, url, news_from_title):
        # 获取来源页html
        resp = self.download.getResponse(redis_client=redis_client, url=url)
        # 获取新闻种子列表
        NewUrlList = self.server.getNewsUrlList_Template_3(resp=resp, news_from_title=news_from_title)
        for NewUrl in NewUrlList:
            LOGGING.info(NewUrl)
            with open('url_data.txt', 'a') as f:
                f.write(str(NewUrl) + '\n')


    # 抓取模板4
    def newsTemplate_4(self, redis_client, news_from_title):
        index_url = 'http://sike.news.cn/page/{}'
        page = 1
        while 1:
            url = index_url.format(page)
            # 获取来源页响应
            resp = self.download.getResponse(redis_client=redis_client, url=url)
            # 获取新闻种子列表
            NewUrlList = self.server.getNewsUrlList_Template_4(resp=resp, news_from_title=news_from_title)
            if not NewUrlList:
                break

            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open('url_data.txt', 'a') as f:
                    f.write(str(NewUrl) + '\n')

            page += 1

    # 抓取模板5
    def newsTemplate_5(self, redis_client, url, news_from_title):
        # 获取来源页响应
        resp = self.download.getResponse(redis_client=redis_client, url=url)
        # 获取栏目分类
        column_type_list = self.server.getColumnTypeList(resp=resp)
        for column_type in column_type_list:
            shuJuXinWenFenLeiUrl = column_type['shuJuXinWenFenLeiUrl']
            shuJuXinWenFenLeiMing = column_type['shuJuXinWenFenLeiMing']
            # 获取分类页响应
            column_type_resp = self.download.getResponse(redis_client=redis_client, url=shuJuXinWenFenLeiUrl)
            # 获取分类pageNid
            pageNid = self.server.getPageNid(resp=column_type_resp)
            if pageNid is None:
                continue
            # 生成新闻列表页首页API
            APIUrl = self.server.createApiUrl(nid=pageNid, page=1, count=16)
            # 获取首页API响应
            APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
            # 获取总页数
            page_sum = self.server.getPageSum(resp=APIUrlResp, select_num=16)
            for page in range(page_sum):
                # 生成新闻列表页API
                APIUrl = self.server.createApiUrl(nid=pageNid, page=page + 1, count=16)
                # 获取首页API响应
                APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
                # 获取新闻种子列表
                NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, news_from_title=news_from_title)
                for NewUrl in NewUrlList:
                    NewUrl['shuJuXinWenFenLeiMing'] = shuJuXinWenFenLeiMing
                    LOGGING.info(NewUrl)
                    with open('url_data.txt', 'a') as f:
                        f.write(str(NewUrl) + '\n')

    # 抓取模板6
    def newsTemplate_6(self, redis_client, news_from_title):
        url = 'http://uav.xinhuanet.com/zx.htm'
        # 获取来源页响应
        resp = self.download.getResponse(redis_client=redis_client, url=url)
        # 获取pageNid
        pageNid = self.server.getPageNid(resp=resp)
        if pageNid is None:
            return
        # 生成新闻列表页首页API
        APIUrl = self.server.createApiUrl(nid=pageNid, page=1, count=20)
        # 获取首页API响应
        APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
        # 获取总页数
        page_sum = self.server.getPageSum(resp=APIUrlResp, select_num=20)
        for page in range(page_sum):
            # 生成新闻列表页API
            APIUrl = self.server.createApiUrl(nid=pageNid, page=page + 1, count=20)
            # 获取首页API响应
            APIUrlResp = self.download.getResponse(redis_client=redis_client, url=APIUrl)
            # 获取新闻种子列表
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, news_from_title=news_from_title)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open('url_data.txt', 'a') as f:
                    f.write(str(NewUrl) + '\n')


    def run(self):
        redis_client = redispool_utils.createRedisPool()
        # 获取首页html源码
        index_resp = self.download.getResponse(redis_client=redis_client, url=self.index_url)
        # 获取新闻来源列表
        news_from_list = self.server.getNewsFromList(resp=index_resp)
        for news_from in news_from_list:
            news_from_title = news_from['laiYuanTitle']
            news_from_url = news_from['laiYuanUrl']

            if news_from_title == '时政':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '财经':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '国际':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '娱乐':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '图片':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '社区':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '军事':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '体育':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '前沿':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '教育':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '网评':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '港澳台':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '法治':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '社会':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '文化':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '时尚':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '旅游':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '健康':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '汽车':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '房产':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '美食':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '悦读':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '视频':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '广播':
                self.newsTemplate_2(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '科普':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '新华社新闻':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '滚动新闻':
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '学习进行时':
                news_from_url = 'http://m.xinhuanet.com/xxjxs/index.htm'
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '人事':
                self.newsTemplate_3(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '思客':
                self.newsTemplate_4(redis_client=redis_client, news_from_title=news_from_title)
            if news_from_title == '数据新闻':
                self.newsTemplate_5(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            if news_from_title == '无人机':
                self.newsTemplate_6(redis_client=redis_client, news_from_title=news_from_title)
            if (news_from_title == '北京' or
                    news_from_title == '吉林' or
                    news_from_title == '上海' or
                    news_from_title == '江苏' or
                    news_from_title == '安徽' or
                    news_from_title == '福建' or
                    news_from_title == '山东' or
                    news_from_title == '湖北' or
                    news_from_title == '湖南' or
                    news_from_title == '广东' or
                    news_from_title == '广西' or
                    news_from_title == '海南' or
                    news_from_title == '重庆' or
                    news_from_title == '四川' or
                    news_from_title == '贵州' or
                    news_from_title == '甘肃' or
                    news_from_title == '宁夏' or
                    news_from_title == '新疆' or
                    news_from_title == '内蒙古' or
                    news_from_title == '黑龙江' or
                    news_from_title == '云南'):
                self.newsTemplate_1(redis_client=redis_client, url=news_from_url, news_from_title=news_from_title)
            else:
                pass


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
