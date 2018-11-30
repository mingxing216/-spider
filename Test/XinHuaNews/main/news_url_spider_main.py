# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
from multiprocessing.dummy import Pool as ThreadPool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Utils import dir_utils
from Test.XinHuaNews.middleware import download_middleware
from Test.XinHuaNews.services import services

log_file_dir = 'XinHuaNews'  # LOG日志存放路径
LOGNAME = '<新华新闻种子爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.download = download_middleware.Download_Middleware(logging=LOGGING)
        self.server = services.Services(logging=LOGGING)
        self.index_url = 'http://m.xinhuanet.com/'
        self.file_path = os.path.dirname(__file__) + os.sep + "../../../" + "Static/txt/" + "XinHuaNewsUrl.txt"


    # 抓取模板1
    def newsTemplate_1(self, redis_client, url, one_clazz):
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
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, one_clazz=one_clazz)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open(self.file_path, 'a') as f:
                    datas = json.dumps(NewUrl)
                    f.write(datas + '\n')
                    # f.write(str(NewUrl) + '\n')

    # 抓取模板2
    def newsTemplate_2(self, redis_client, url, one_clazz):
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
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, one_clazz=one_clazz)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open(self.file_path, 'a') as f:
                    f.write(str(NewUrl) + '\n')

    # 抓取模板3
    def newsTemplate_3(self, redis_client, url, one_clazz):
        # 获取来源页html
        resp = self.download.getResponse(redis_client=redis_client, url=url)
        # 获取新闻种子列表
        NewUrlList = self.server.getNewsUrlList_Template_3(resp=resp, one_clazz=one_clazz)
        for NewUrl in NewUrlList:
            LOGGING.info(NewUrl)
            with open(self.file_path, 'a') as f:
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
                with open(self.file_path, 'a') as f:
                    f.write(str(NewUrl) + '\n')

            page += 1

    # 抓取模板5
    def newsTemplate_5(self, redis_client, url, one_clazz):
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
                NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, one_clazz=one_clazz)
                for NewUrl in NewUrlList:
                    NewUrl['last_from_title'] = shuJuXinWenFenLeiMing
                    LOGGING.info(NewUrl)
                    with open(self.file_path, 'a') as f:
                        f.write(str(NewUrl) + '\n')

    # 抓取模板6
    def newsTemplate_6(self, redis_client, one_clazz):
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
            NewUrlList = self.server.getNewUrlList(resp=APIUrlResp, one_clazz=one_clazz)
            for NewUrl in NewUrlList:
                LOGGING.info(NewUrl)
                with open(self.file_path, 'a') as f:
                    f.write(str(NewUrl) + '\n')

    def handle(self, redis_client, news_from):
        one_clazz = news_from['laiYuanTitle']
        news_from_url = news_from['laiYuanUrl']

        if one_clazz == '时政':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '财经':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '国际':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '娱乐':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '图片':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '军事':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '体育':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '教育':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '网评':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '港澳台':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '法治':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '社会':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '文化':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '时尚':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '旅游':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '健康':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '汽车':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '房产':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '美食':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '悦读':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '视频':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '新华社新闻':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        if one_clazz == '滚动新闻':
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        # if one_clazz == '人事':
        #     self.newsTemplate_3(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        # if one_clazz == '思客':
        #     self.newsTemplate_4(redis_client=redis_client, one_clazz=one_clazz)
        # if one_clazz == '数据新闻':
        #     self.newsTemplate_5(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        # if one_clazz == '无人机':
        #     self.newsTemplate_6(redis_client=redis_client, one_clazz=one_clazz)
        if (one_clazz == '北京' or
                one_clazz == '吉林' or
                one_clazz == '上海' or
                one_clazz == '江苏' or
                one_clazz == '安徽' or
                one_clazz == '福建' or
                one_clazz == '山东' or
                one_clazz == '湖北' or
                one_clazz == '湖南' or
                one_clazz == '广东' or
                one_clazz == '广西' or
                one_clazz == '海南' or
                one_clazz == '重庆' or
                one_clazz == '四川' or
                one_clazz == '贵州' or
                one_clazz == '甘肃' or
                one_clazz == '宁夏' or
                one_clazz == '新疆' or
                one_clazz == '内蒙古' or
                one_clazz == '黑龙江' or
                one_clazz == '云南'):
            self.newsTemplate_1(redis_client=redis_client, url=news_from_url, one_clazz=one_clazz)
        else:
            pass

    def run(self):
        try:
            dir_utils.deleteFile(self.file_path)
        except:
            pass
        redis_client = redispool_utils.createRedisPool()
        # 获取首页html源码
        index_resp = self.download.getResponse(redis_client=redis_client, url=self.index_url)
        # 获取新闻来源列表
        news_from_list = self.server.getNewsFromList(resp=index_resp)

        threadpool = ThreadPool(4)
        for news_from in news_from_list:
            threadpool.apply_async(func=self.handle, args=(redis_client, news_from))
        threadpool.close()
        threadpool.join()


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
