# -*-coding:utf-8-*-

'''

'''
import sys
import os
import hashlib
import base64
import pprint
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
from Test.XinHuaNews.services import services
from Test.XinHuaNews.dao import dao
from Test.XinHuaNews.middleware import download_middleware

log_file_dir = 'XinHuaNews'  # LOG日志存放路径
LOGNAME = '<新华新闻数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.file_path = os.path.dirname(__file__) + os.sep + "../../../" + "Static/txt/" + "XinHuaNewsUrl.txt"
        self.server = services.NewsDataSpiderServices(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING)

        self.download = download_middleware.Download_Middleware(logging=LOGGING)

    # 抓取模板1
    def newsTemplate_1(self, redis_client, mysql_client, new_url_data):
        save_data = {}
        one_clazz = new_url_data['one_clazz']
        new_url = new_url_data['new_url']
        zhaiYao = new_url_data['zhaiYao']
        faBuShiJian = new_url_data['faBuShiJian']
        title = new_url_data['title']
        biaoQian = new_url_data['biaoQian']
        zhaiYaoTu = new_url_data['zhaiYaoTu']
        # 查询新闻是否被抓取过, True(抓过)、False(未抓过)
        status = self.dao.new_status(mysql_client=mysql_client, new_url=new_url)
        if status is True:
            return
        # 获取新闻页html源码
        resp = self.download.getResponse(redis_client=redis_client, url=new_url)
        # 获取来源网站
        laiYuanWangZhan = self.server.newsTemplate_1_LaiYuanWangZhan(resp)
        if laiYuanWangZhan is None:
            laiYuanWangZhan = ''
            with open('没有来源网站的新闻.txt', 'a') as f:
                f.write(new_url + '\n')
        # 获取正文
        zhengWen = self.server.newsTemplate_1_ZhengWen(resp)
        if zhengWen is None:
            zhengWen = ''
            with open('没有正文的新闻.txt', 'a') as f:
                f.write(new_url + '\n')
        # 获取组图列表url
        img_url_data = self.server.newsTemplate_1_ZuTu(resp=resp, new_url=new_url)
        if img_url_data:
            for img_url in img_url_data:
                # 下载图片
                img_resp = self.download.down_img(redis_client=redis_client, url=img_url)
                img_data_bs64 = base64.b64encode(img_resp)
                # 存储图片
                sha = hashlib.sha1(img_url.encode('utf-8')).hexdigest()
                # LOGGING.info('图片sha: {}'.format(sha))
                item = {
                    'pk': sha,
                    'type': 'image',
                    'url': img_url
                }
                self.dao.saveImg(media_url=img_url, content=img_data_bs64, type='image', item=item)
        if img_url_data:
            # 替换正文中的图片url地址
            zhengWen = self.server.newsTemplate_1_UpdateZhengWen(zhengWen=zhengWen, img_url_list=img_url_data)
        # 获取责任编辑
        zeRenBianJi = self.server.newsTemplate_1_ZeRenBianJi(resp=resp, url=new_url)
        if zeRenBianJi is None:
            zeRenBianJi = ''
            with open('没有责任编辑的新闻.txt', 'a') as f:
                f.write(new_url + '\n')
        # 获取视频
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
        ss = '新闻'
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
        save_data['zhaiYaoTu'] = zhaiYaoTu
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

        pprint.pprint(save_data)


    def handle(self, redis_client, mysql_client, new_url_data):
        one_clazz = new_url_data['one_clazz']
        if one_clazz == '时政':
            self.newsTemplate_1(redis_client=redis_client, mysql_client=mysql_client, new_url_data=new_url_data)

    def run(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        # 获取新闻种子数据
        new_url_data_list = self.server.getUrlDataList(filepath=self.file_path)
        for new_url_data in new_url_data_list:
            if new_url_data['one_clazz'] == '时政':
                self.handle(redis_client=redis_client, mysql_client=mysql_client, new_url_data=new_url_data)
            else:
                continue
        # threadpool = ThreadPool(1)
        # for new_url_data in new_url_data_list:
        #     threadpool.apply_async(func=self.handle, args=(redis_client, mysql_client, new_url_data))
        # threadpool.close()
        # threadpool.join()


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
