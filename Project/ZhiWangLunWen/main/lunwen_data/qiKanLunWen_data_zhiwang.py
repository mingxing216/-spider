# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import hashlib
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_期刊论文_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_LunWenDataServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        for i in range(10):
            resp = self.download_middleware.getResp(url=url,
                                                    mode=mode,
                                                    s=s,
                                                    data=data,
                                                    cookies=cookies,
                                                    referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text or len(response.text) < 200:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            return None

    def imgDownload(self, img_task):
        # 获取图片响应
        media_resp = self.__getResp(url=img_task['url'], mode='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_task['url']))
            # 存储图片种子
            img_task['img_dict']['bizTitle'] = img_task['img_dict']['bizTitle'].replace('"', '\\"').replace("'", "''")
            img_task['img_dict']['bizDesc'] = img_task['img_dict']['bizDesc'].replace('"', '\\"').replace("'", "''")
            self.dao.saveTaskToMysql(table=config.MYSQL_IMG, memo=img_task['img_dict'], ws='中国知网', es='论文')
            return
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=img_task['sha'])

        img_content = media_resp.content
        # 存储图片
        self.dao.saveMediaToHbase(media_url=img_task['url'], content=img_content, item=img_task['img_dict'],
                                  type='image')

    def handle(self, task, save_data):
        # 获取task数据
        task_data = self.server.getTask(task)
        # print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        qiKanUrl = task_data['qiKanUrl']
        xueKeLeiBie = task_data['xueKeLeiBie']

        # url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=XZLD2008Z1007&tableName=CJFDN0508'
        # 查询当前文章是否被抓取过
        status = self.dao.getTaskStatus(sha=sha)

        if status is False:
            # 获取文章页html源码
            article_html = self.__getResp(url=url, mode='get')
            if not article_html:
                LOGGING.error('获取论文详情页html源码失败，url: {}'.format(url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
                return

            # article_html = resp.text

            # ========================获取数据==========================
            # 获取文章标题
            save_data['title'] = self.server.getArticleTitle(article_html)
            # 获取作者
            save_data['zuoZhe'] = self.server.getZuoZhe(article_html)
            # 获取作者单位
            save_data['faBuDanWei'] = self.server.getZuoZheDanWei(article_html)
            # 获取摘要
            save_data['zhaiYao'] = self.server.getZhaiYao(article_html)
            # 获取基金
            save_data['jiJin'] = self.server.getJiJin(article_html)
            # 获取关键词
            save_data['guanJianCi'] = self.server.getGuanJianCi(article_html)
            # 获取doi
            save_data['DOI'] = self.server.getDoi(article_html)
            # 获取中图分类号
            save_data['zhongTuFenLeiHao'] = self.server.getZhongTuFenLeiHao(article_html)
            # 获取组图链接
            picUrls = self.server.getPicUrls(download_middleware=self.download_middleware,
                                             resp=article_html)
            # print(picUrls)
            if picUrls:
                # 获取内容(关联组图)
                save_data['relationPics'] = self.server.guanLianPics(url, sha)
                # 组图实体
                pics = {}
                # 标题
                pics['title'] = save_data['title']
                # 组图内容
                pics['labelObj'] = self.server.getPics(picUrls, title=pics['title'])
                # print(pics['labelObj'])
                # 关联论文
                pics['picsRelationParent'] = self.server.guanLianLunWen(url, sha)
                # url
                pics['url'] = url
                # 生成key
                pics['key'] = url
                # 生成sha
                pics['sha'] = hashlib.sha1(pics['key'].encode('utf-8')).hexdigest()
                # 生成ss ——实体
                pics['ss'] = '组图'
                # 生成es ——栏目名称
                pics['es'] = '论文'
                # 生成ws ——目标网站
                pics['ws'] = '中国知网'
                # 生成clazz ——层级关系
                pics['clazz'] = '组图_实体'
                # 生成biz ——项目
                pics['biz'] = '文献大数据'
                # 生成ref
                pics['ref'] = ''
                # 保存组图实体到Hbase
                self.dao.saveDataToHbase(data=pics)

                # 创建图片任务列表
                img_tasks = []

                # 下载图片
                for img_url in picUrls:
                    dict = {}
                    dict['url'] = img_url['url']
                    dict['img_dict'] = {}
                    dict['img_dict']['bizDesc'] = img_url['desc']
                    dict['img_dict']['bizTitle'] = save_data['title']
                    dict['img_dict']['relEsse'] = self.server.guanLianLunWen(url, sha)
                    dict['img_dict']['relPics'] = self.server.guanLianPics(url, sha)
                    img_tasks.append(dict)

                # 创建gevent协程
                img_list = []
                for img_task in img_tasks:
                    s = gevent.spawn(self.imgDownload, img_task)
                    img_list.append(s)
                gevent.joinall(img_list)

                # 创建线程池
                # threadpool = ThreadPool()
                # for img_task in img_tasks:
                #     threadpool.apply_async(func=self.imgDownload, args=(img_task,))
                #
                # threadpool.close()
                # threadpool.join()

            else:
                # 获取内容(关联组图)
                save_data['relationPics'] = {}
            # 获取期刊名称
            save_data['qiKanMingCheng'] = self.server.getQiKanMingCheng(article_html)
            # 获取期号
            save_data['qiHao'] = self.server.getQiHao(article_html)
            # 获取下载PDF下载链接
            save_data['xiaZai'] = self.server.getXiaZai(article_html)
            # 获取在线阅读
            save_data['zaiXianYueDu'] = self.server.getZaiXianYueDu(article_html)
            # 获取下载次数
            save_data['xiaZaiCiShu'] = self.server.getXiaZaiCiShu(article_html)
            # 获取所在页码
            save_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(article_html)
            # 获取页数
            save_data['yeShu'] = self.server.getYeShu(article_html)
            # 获取大小
            save_data['daXiao'] = self.server.getDaXiao(article_html)
            # 获取时间【年】
            save_data['shiJian'] = self.server.getshiJian(article_html)
            # 学科类别
            save_data['xueKeLeiBie'] = xueKeLeiBie
            # 来源分类
            save_data['laiYuanFenLei'] = ""
            # 获取参考文献
            save_data['guanLianCanKaoWenXian'] = self.server.getGuanLianCanKaoWenXian(
                download_middleware=self.download_middleware,
                url=url)
            # 获取关联文档
            save_data['guanLianWenDang'] = {}
            # 获取关联人物
            save_data['guanLianRenWu'] = self.server.getGuanLianRenWu(article_html)
            # 获取关联企业机构
            save_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)
            # 获取关联图书期刊
            save_data['guanLianTuShuQiKan'] = self.server.getGuanLianTuShuQiKan(qiKanUrl)

            # ============================ 公共字段
            # url
            save_data['url'] = url
            # 生成key
            save_data['key'] = url
            # 生成sha
            save_data['sha'] = sha
            # 生成ss ——实体
            save_data['ss'] = '论文'
            # 生成es ——栏目名称
            save_data['es'] = '期刊论文'
            # 生成ws ——目标网站
            save_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            save_data['clazz'] = '论文_期刊论文'
            # 生成biz ——项目
            save_data['biz'] = '文献大数据'
            # 生成ref
            save_data['ref'] = ''

            # --------------------------
            # 存储部分
            # --------------------------
            # 保存人物种子
            if save_data['guanLianRenWu']:
                for people in save_data['guanLianRenWu']:
                    # people['shijian'] = save_data['shiJian']
                    self.dao.saveTaskToMysql(table=config.MYSQL_PEOPLE, memo=people, ws='中国知网', es='论文')
            # 保存机构种子
            if save_data['guanLianQiYeJiGou']:
                for intitute in save_data['guanLianQiYeJiGou']:
                    self.dao.saveTaskToMysql(table=config.MYSQL_INSTITUTE, memo=intitute, ws='中国知网', es='论文')

            # # 记录已抓取任务
            # self.dao.saveComplete(table=config.MYSQL_REMOVAL, sha=sha)
            return sha

        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)

    def run(self, task):
        # 创建数据存储字典
        save_data = {}
        # 获取字段值存入字典并返回sha
        sha = self.handle(task=task, save_data=save_data)
        # 保存数据到Hbase
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        # 存储数据
        success = self.dao.saveDataToHbase(data=save_data)
        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_QIKANLUNWEN_PAPER, count=20, lockname=config.REDIS_QIKANLUNWEN_PAPER_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # 创建线程池
                # threadpool = ThreadPool()
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
                #
                # threadpool.close()
                # threadpool.join()
                #
                # time.sleep(1)

            else:
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"url": "http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=JZCK201810032&tableName=CJFDLAST2018", "qiKanUrl": "http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JZCK", "xueKeLeiBie": "信息科技_自动化技术"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
