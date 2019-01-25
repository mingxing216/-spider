# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
from multiprocessing import Pool as Process

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
from ObjectBeas.XinHuaNews.services import services
from ObjectBeas.XinHuaNews.dao import dao
from ObjectBeas.XinHuaNews.middleware import download_middleware

log_file_dir = 'XinHuaNews'  # LOG日志存放路径
LOGNAME = '<新华新闻数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.file_path = os.path.dirname(__file__) + os.sep + "../../../" + "Static/txt/" + "XinHuaNewsUrl.txt"

    # 抓取模板1
    def newsTemplate_1(self, redis_client, mysql_client, new_url_data):
        save_data = {}
        one_clazz = new_url_data['one_clazz']
        new_url = new_url_data['new_url']
        zhaiYao = new_url_data['zhaiYao']
        faBuShiJian = new_url_data['faBuShiJian']
        title = new_url_data['title']
        biaoShi = new_url_data['biaoShi']
        # new_url = 'http://www.xinhuanet.com/politics/2018-11/19/c_1123731703.htm'
        # # 查询新闻是否被抓取过, True(抓过)、False(未抓过)
        # status = dao.new_status(mysql_client=mysql_client, new_url=new_url)
        # if status is True:
        #     return
        # 获取新闻页html源码
        resp = download_middleware.getResponse(logging=LOGGING, redis_client=redis_client, url=new_url)

        # 下载标识
        if biaoShi != '':
            img_resp = download_middleware.down_img(logging=LOGGING, redis_client=redis_client, url=biaoShi)
            if img_resp is not None:
                # 存储图片到hbase
                dao.saveImg(logging=LOGGING, media_url=biaoShi, content=img_resp, type='image')

        # 获取来源网站
        laiYuanWangZhan = services.newsTemplate_1_LaiYuanWangZhan(resp)
        if laiYuanWangZhan is None:
            laiYuanWangZhan = ''
            with open('没有来源网站的新闻.txt', 'a') as f:
                f.write(new_url + '\n')

        # 获取正文
        zhengWen = ''
        zhengWen_list = services.newsTemplate_1_ZhengWen(logging=LOGGING, redis_client=redis_client, url=new_url)
        if not zhengWen_list:
            zhengWen = ''
            with open('没有正文的新闻.txt', 'a') as f:
                f.write(new_url + '\n')
        else:
            for data in zhengWen_list:
                zhengWen += data['zhengWen']

        # 获取标签
        biaoQian = services.newsTemplate_1_BiaoQian(resp)
        if biaoQian is None:
            biaoQian = ''
            with open('没有标签的新闻.txt', 'a') as f:
                f.write(new_url + '\n')

        # 获取责任编辑
        zeRenBianJi = services.newsTemplate_1_ZeRenBianJi(resp=resp)
        if zeRenBianJi is None:
            zeRenBianJi = ''
            with open('没有责任编辑的新闻.txt', 'a') as f:
                f.write(new_url + '\n')
        # 获取视频
        shiPin = services.newsTemplate_1_ShiPin(resp=resp, url=new_url)
        if shiPin is None:
            shiPin = ''

        # 获取发布者
        faBuZhe = ''
        # 获取编辑
        bianJi = ''
        # 获取设计
        sheJi = ''
        # 生成新闻url
        url = new_url
        # 生成key
        key = new_url
        # 生成sha
        sha = hashlib.sha1(new_url.encode('utf-8')).hexdigest()
        # 生成ss ——实体
        ss = '资讯'
        # 生成ws ——目标网站
        ws = '新华网'
        # 生成clazz ——层级关系
        clazz = '资讯_{}'.format(one_clazz)
        # 生成es ——栏目名称
        es = one_clazz
        # 生成biz ——项目
        biz = '文献大数据'
        # 生成ref
        ref = ''
        save_data['new_url'] = new_url
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
        save_data['url'] = url
        save_data['key'] = key
        save_data['sha'] = sha
        save_data['ss'] = ss
        save_data['ws'] = ws
        save_data['clazz'] = clazz
        save_data['es'] = es
        save_data['biz'] = biz
        save_data['ref'] = ref

        LOGGING.info(sha)

        # 存储数据
        dao.saveData(data=save_data, logging=LOGGING)

    def handle(self, new_url_data):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        one_clazz = new_url_data['one_clazz']
        if one_clazz == '时政':
            self.newsTemplate_1(redis_client=redis_client, mysql_client=mysql_client, new_url_data=new_url_data)
        # if one_clazz == '财经':
        #     self.newsTemplate_1(redis_client=redis_client, mysql_client=mysql_client, new_url_data=new_url_data)

    def run(self):

        # 获取新闻种子数据
        new_url_data_list = services.getUrlDataList(filepath=self.file_path)

        # for new_url_data in new_url_data_list:
        #     self.handle(new_url_data=new_url_data)
        #     break

        po = Process(int(settings.XINHUA_NEWS_DATA_SPIDER_PROCESS))
        for new_url_data in new_url_data_list:
            po.apply_async(func=self.handle, args=(new_url_data, ))
        po.close()
        po.join()


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
