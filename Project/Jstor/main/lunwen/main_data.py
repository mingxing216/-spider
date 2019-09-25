# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
# 猴子补丁一定要先打，不然就会报错
monkey.patch_all()
import sys
import os
import time
import copy
import traceback
import hashlib
import datetime
import requests
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Jstor.middleware import download_middleware
from Project.Jstor.service import service
from Project.Jstor.dao import dao
from Project.Jstor import config

log_file_dir = 'Jstor'  # LOG日志存放路径
LOGNAME = 'Jstor_期刊论文_data'  # LOG名
NAME = 'Jstor_期刊论文_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_LunWenServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.cookie_dict = ''

    def __getResp(self, func, url, mode, data=None, cookies=None):
        # while 1:
        # 发现验证码，最多访问页面10次
        for i in range(10):
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None
        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return None

    def imgDownload(self, img_task):
        # 获取图片响应
        media_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=img_task['url'],
                                    mode='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_task['url']))
            # 存储图片种子
            img_task['img_dict']['bizTitle'] = img_task['img_dict']['bizTitle'].replace('"', '\\"').replace("'", "''")
            self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_task['img_dict'])
            return
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=img_task['sha'])

        img_content = media_resp.text
        # 存储图片
        self.dao.saveMediaToHbase(media_url=img_task['url'], content=img_content, item=img_task['img_dict'], type='image')

    # 模板1
    def templateOne(self, save_data, script, url, sha):
        # 获取标题
        save_data['title'] = self.server.getField(script, 'displayTitle')
        # 获取作者
        save_data['zuoZhe'] = self.server.getMoreField(script, 'authors')
        # 获取期刊名称
        save_data['qiKanMingCheng'] = self.server.getField(script, 'journal')
        # 获取DOI
        save_data['DOI'] = self.server.getField(script, 'doi')
        # 获取ISSN
        save_data['ISSN'] = self.server.getField(script, 'issn')
        # 获取卷期
        save_data['juanQi'] = self.server.getJuanQi(script)
        # 获取时间
        shijian = self.server.getField(script, 'publishedDate')
        if shijian:
            try:
                save_data['shiJian'] = str(datetime.datetime.strptime(shijian, '%B %Y'))
            except:
                save_data['shiJian'] = shijian
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getField(script, 'pageRange')
        # 获取页数
        save_data['yeShu'] = self.server.getField(script, 'pageCount')
        # 获取出版商
        save_data['chuBanShang'] = self.server.getChuBanShang(script)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(script)
        # 获取所有图片链接
        picUrl = self.server.getPicUrl(script)
        if picUrl:
            # 获取内容(关联组图)
            save_data['relationPics'] = self.server.guanLianPics(url)
            # 组图实体
            pics = {}
            # 标题
            pics['title'] = save_data['title']
            # 组图内容
            pics['labelObj'] = self.server.getPics(script, title=pics['title'])
            # 关联论文
            pics['picsRelationParent'] = self.server.guanLianLunWen(url)
            # url
            pics['url'] = url
            # 生成key
            pics['key'] = url
            # 生成sha
            pics['sha'] = hashlib.sha1(pics['key'].encode('utf-8')).hexdigest()
            # 生成ss ——实体
            pics['ss'] = '组图'
            # 生成ws ——目标网站
            pics['ws'] = 'JSTOR'
            # 生成clazz ——层级关系
            pics['clazz'] = '组图_实体'
            # 生成es ——栏目名称
            pics['es'] = 'Journals'
            # 生成biz ——项目
            pics['biz'] = '文献大数据'
            # 生成ref
            pics['ref'] = ''
            # 保存组图实体到Hbase
            self.dao.saveDataToHbase(data=pics)

            # 创建图片任务列表
            img_tasks = []

            # 下载图片
            for img_url in picUrl:
                dict = {}
                dict['url'] = img_url
                dict['sha'] = sha
                dict['img_dict'] = {}
                dict['img_dict']['url'] = img_url
                dict['img_dict']['bizTitle'] = save_data['title']
                dict['img_dict']['relEsse'] = self.server.guanLianLunWen(url)
                dict['img_dict']['relPics'] = self.server.guanLianPics(url)
                img_tasks.append(dict)

            # 创建gevent协程
            img_list = []
            for img_task in img_tasks:
                s = gevent.spawn(self.imgDownload, img_task)
                img_list.append(s)
            gevent.joinall(img_list)

            # # 创建线程池
            # threadpool = ThreadPool()
            # for img_task in img_tasks:
            #     threadpool.apply_async(func=self.imgDownload, args=(img_task,))
            #
            # threadpool.close()
            # threadpool.join()

        else:
            # 获取内容(关联组图)
            save_data['relationPics'] = {}
        # 获取关键词
        save_data['guanJianCi'] = self.server.getMoreField(script, 'topics')
        # 获取参考文献
        save_data['canKaoWenXian'] = self.server.getCanKaoWenXian(script)
        # 获取关联期刊
        save_data['guanLianQiKan'] = self.server.getGuanLianQiKan(script)
        # 存储期刊种子
        if save_data['guanLianQiKan']:
            self.dao.saveProjectUrlToMysql(table=config.MYSQL_MAGAZINE, memo=save_data['guanLianQiKan'])
        # 获取关联文档
        save_data['guanLianWenDang'] = self.server.getGuanLianWenDang(script)
        if save_data['guanLianWenDang']:
            # 深拷贝关联文档字典，目的为了修改拷贝的内容后，原文档字典不变
            document = copy.deepcopy(save_data['guanLianWenDang'])
            document['lunWenUrl'] = url
            document['title'] = save_data['title'].replace('"', '\\"').replace("'", "''")
            # 存储文档种子
            self.dao.saveProjectUrlToMysql(table=config.MYSQL_DOCUMENT, memo=document)

    # 模板2
    def templateTwo(self, save_data, select, html):
        # 获取标题
        save_data['title'] = self.server.getTitle(select)
        # 获取作者
        save_data['zuoZhe'] = self.server.getZuoZhe(select)
        # 获取期刊名称
        save_data['qiKanMingCheng'] = self.server.getQiKanMingCheng(select)
        # 获取DOI
        save_data['DOI'] = ""
        # 获取ISSN
        save_data['ISSN'] = self.server.getIssn(select)
        # 获取卷期
        save_data['juanQi'] = self.server.getJuanQis(select)
        # 获取时间
        save_data['shiJian'] = ""
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(select)
        # 获取页数
        save_data['yeShu'] = self.server.getYeShu(select)
        # 获取出版商
        save_data['chuBanShang'] = self.server.getChuBanShangs(select)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYaos(html)
        # 获取内容(关联组图)
        save_data['relationPics'] = {}
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(select)
        # 获取参考文献
        save_data['canKaoWenXian'] = []
        # 获取关联期刊
        save_data['guanLianQiKan'] = self.server.getGuanLianQiKans(select)
        # 存储期刊种子
        if save_data['guanLianQiKan']:
            self.dao.saveProjectUrlToMysql(table=config.MYSQL_MAGAZINE, memo=save_data['guanLianQiKan'])
        # 获取关联文档
        save_data['guanLianWenDang'] = {}



    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)

        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        xueKeLeiBie = task_data['xueKeLeiBie']

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET',
                              cookies=self.cookie_dict)
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        response = resp.text
        # print(response)
        # 获取script标签内容
        script = self.server.getScript(response)
        # print(script)

        # 转为selector选择器
        selector = self.server.getSelector(response)

        # 如果script标签中有内容，执行第一套模板
        if script:
            self.templateOne(save_data=save_data, script=script, url=url, sha=sha)
        # 如果能从页面直接获取标题，执行第二套模板
        else:
            self.templateTwo(save_data=save_data, select=selector, html=response)

        # ===================公共字段
        # 获取学科类别
        save_data['xueKeLeiBie'] = xueKeLeiBie
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成ws ——目标网站
        save_data['ws'] = 'JSTOR'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_期刊论文'
        # 生成es ——栏目名称
        save_data['es'] = 'Journals'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # 返回sha为删除任务做准备
        return sha

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

        self.dao.saveDataToHbase(data=save_data)

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_PAPER, count=10, lockname=config.REDIS_PAPER_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))
            # print(task_list)

            if task_list:
                # 获取cookie
                self.cookie_dict = self.download_middleware.create_cookie()
                # cookie创建失败，重新创建
                if not self.cookie_dict:
                    continue

                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # 创建gevent协程
                g_list = []
                for task in task_list:
                    s = gevent.spawn(self.run, task)
                    g_list.append(s)
                gevent.joinall(g_list)

                # # 创建线程池
                # threadpool = ThreadPool()
                # for task in task_list:
                #     threadpool.apply_async(func=self.run, args=(task,))
                #
                # threadpool.close()
                # threadpool.join()

                time.sleep(1)
            else:
                time.sleep(2)
                continue
                # LOGGING.info('队列中已无任务，结束程序')
                # return

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{"url": "https://www.jstor.org/stable/44744545?Search=yes&resultItemClick=true&&searchUri=%2Fdfr%2Fresults%3Fpagemark%3DcGFnZU1hcms9OA%253D%253D%26amp%3BsearchType%3DfacetSearch%26amp%3Bcty_journal_facet%3Dam91cm5hbA%253D%253D%26amp%3Bsd%3D1873%26amp%3Bed%3D1874%26amp%3Bacc%3Ddfr%26amp%3Bdisc_literature-discipline_facet%3DbGl0ZXJhdHVyZS1kaXNjaXBsaW5l&ab_segments=0%2Fdefault-2%2Fcontrol&seq=1#metadata_info_tab_contents", "xueKeLeiBie": "Anthropology"}')
    except:
        LOGGING.error(str(traceback.format_exc()))

if __name__ == '__main__':
    begin_time = time.time()

    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    #
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
