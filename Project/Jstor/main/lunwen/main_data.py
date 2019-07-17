# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import copy
import traceback
import hashlib
import datetime
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Jstor.middleware import download_middleware
from Project.Jstor.service import service
from Project.Jstor.dao import dao
from Project.Jstor import config

log_file_dir = 'Jstor'  # LOG日志存放路径
LOGNAME = '<Jstor_期刊论文_data>'  # LOG名
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
        # self.cookie_dict = ''

    def __getResp(self, func, url, mode, data=None, cookies=None):
        # while 1:
        # 最多访问页面10次
        for i in range(10):
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None
        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return None

    # 模板1
    def templateOne(self, save_data, script, url):
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
        # 获取内容
        save_data['neiRong'] = self.server.getPics(script)
        # 下载图片
        if save_data['neiRong']:
            for img_url in save_data['neiRong']:
                title = save_data['title']
                relation = {
                    'url': url,
                    'sha': hashlib.sha1(url.encode('utf-8')).hexdigest(),
                    'ss': '论文'
                }
                img_dict = {}
                img_dict['bizTitle'] = title
                img_dict['relEsse'] = relation
                img_dict['url'] = img_url
                # 存储图片种子
                self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
                # # 获取真正图片url链接
                # media_resp = self.__getResp(func=self.download_middleware.getResp, url=img_url, mode='GET')
                # img_content = media_resp.text
                # # 存储图片
                self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')

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
            document['title'] = save_data['title']
            # 存储文档种子
            self.dao.saveProjectUrlToMysql(table=config.MYSQL_DOCUMENT, memo=document)

    # 模板2
    def templateTwo(self, save_data, select, html):
        # 获取标题
        save_data['title'] = self.server.getTitle(select)
        # 获取作者
        save_data['zuoZhe'] = self.server.getZuoZhe(select)
        # 获取期刊名称
        save_data['qiKanMingCheng'] = ''
        # 获取DOI
        save_data['DOI'] = ''
        # 获取ISSN
        save_data['ISSN'] = self.server.getIssn(select)
        # 获取卷期
        save_data['juanQi'] = self.server.getJuanQis(select)
        # 获取时间
        save_data['shiJian'] = ''
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(select)
        # 获取页数
        save_data['yeShu'] = self.server.getYeShu(select)
        # 获取出版商
        save_data['chuBanShang'] = self.server.getChuBanShangs(select)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYaos(html)
        # 获取内容
        save_data['neiRong'] = ''
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(select)
        # 获取参考文献
        save_data['canKaoWenXian'] = ''
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

        # 获取cookie
        self.cookie_dict = self.download_middleware.create_cookie()
        # cookie创建失败，停止程序
        if not self.cookie_dict:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        # 获取页面响应
        resp = self.__getResp(func=self.download_middleware.getResp,
                              url=url,
                              mode='GET',
                              cookies=self.cookie_dict)
        if not resp:
            LOGGING.error('页面响应获取失败, url: {}'.format(url))
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
            self.templateOne(save_data=save_data, script=script, url=url)
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
        self.dao.saveDataToHbase(data=save_data)

        # 删除任务
        self.dao.deleteTask(table=config.MYSQL_PAPER, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_PAPER, count=100, lockname=config.REDIS_PAPER_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            # 创建线程池
            threadpool = ThreadPool()
            for task in task_list:
                threadpool.apply_async(func=self.run, args=(task,))

            threadpool.close()
            threadpool.join()

            time.sleep(1)


def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task='{\"url\": \"https://www.jstor.org/stable/42816994?Search=yes&resultItemClick=true&&searchUri=%2Fdfr%2Fresults%3Fpagemark%3DcGFnZU1hcms9MzY%253D%26amp%3BsearchType%3DfacetSearch%26amp%3Bcty_journal_facet%3Dam91cm5hbA%253D%253D%26amp%3Bsd%3D1908%26amp%3Bed%3D1909%26amp%3Bacc%3Ddfr%26amp%3Bdisc_education-discipline_facet%3DZWR1Y2F0aW9uLWRpc2NpcGxpbmU%253D&ab_segments=0%2Fdefault-2%2Fcontrol&seq=1#metadata_info_tab_contents\", \"xueKeLeiBie\": \"Education\"}')
        # main.run(task='{\"url\": \"https://www.jstor.org/stable/43691751?Search=yes&resultItemClick=true&&searchUri=%2Fdfr%2Fresults%3FsearchType%3DfacetSearch%26amp%3Bcty_journal_facet%3Dam91cm5hbA%253D%253D%26amp%3Bsd%3D2001%26amp%3Bed%3D2002%26amp%3Bpagemark%3DcGFnZU1hcms9MTg%253D%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr%26amp%3Bacc%3Ddfr&ab_segments=0%2Fdefault-2%2Fcontrol\", \"xueKeLeiBie\": \"abc\"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()

    po = Pool(1)
    for i in range(1):
        po.apply_async(func=process_start)

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)

    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
