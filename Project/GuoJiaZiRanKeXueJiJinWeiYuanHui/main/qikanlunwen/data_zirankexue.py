# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import traceback
import hashlib
import requests
from datetime import datetime
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config


log_file_dir = 'ZiRanKeXue'  # LOG日志存放路径
LOGNAME = '<国家自然科学_论文_data>'  # LOG名
NAME = '国家自然科学_论文_data'  # 爬虫名
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
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.profile_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperInfo'

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    # 获取文档实体字段
    def document(self, pdf_dict, url, sha):
        # 文档数据存储字典
        doc_data = {}

        # 获取标题
        doc_data['title'] = pdf_dict['bizTitle']
        # 获取URL
        doc_data['URL'] = pdf_dict['url']
        # 获取格式
        doc_data['geShi'] = ""
        # 获取大小
        doc_data['daXiao'] = ""
        # 获取标签
        doc_data['biaoQian'] = ""
        # 获取来源网站
        doc_data['laiYuanWangZhan'] = ""
        # 关联论文
        doc_data['guanLianLunWen'] = self.server.guanLianLunWen(url=url, sha=sha)

        # ===================公共字段
        # url
        doc_data['url'] = pdf_dict['url']
        # 生成key
        doc_data['key'] = pdf_dict['url']
        # 生成sha
        doc_data['sha'] = pdf_dict['sha']
        # 生成ss ——实体
        doc_data['ss'] = '文档'
        # 生成es ——栏目名称
        doc_data['es'] = '论文'
        # 生成ws ——目标网站
        doc_data['ws'] = '国家自然科学基金委员会'
        # 生成clazz ——层级关系
        doc_data['clazz'] = '文档_论文文档'
        # 生成biz ——项目
        doc_data['biz'] = '文献大数据_论文'
        # 生成ref
        doc_data['ref'] = ''

        # 保存数据到Hbase
        sto = self.dao.saveDataToHbase(data=doc_data)

        if sto:
            LOGGING.info('文档数据存储成功, sha: {}'.format(pdf_dict['sha']))
        else:
            LOGGING.error('文档数据存储失败, url: {}'.format(pdf_dict['url']))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)

        # 获取页面响应
        pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET')
        if not pdf_resp:
            LOGGING.error('文档响应失败, url: {}'.format(pdf_dict['url']))
            # 标题内容调整格式
            pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储文档种子
            self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')

            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return
        # media_resp.encoding = media_resp.apparent_encoding
        pdf_content = pdf_resp.content
        # with open('profile.pdf', 'wb') as f:
        #     f.write(pdf_resp)
        # 存储文档
        succ = self.dao.saveMediaToHbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict, type='document')
        if not succ:
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            # 标题内容调整格式
            pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储图片种子
            self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        id = task_data['id']
        xueKeLeiBie = task_data['xueKeLeiBie']

        data = {'achievementID': id}
        # 获取页面响应
        resp = self.__getResp(url=self.profile_url, method='POST', data=json.dumps(data))
        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        resp.encoding = resp.apparent_encoding
        resp_json = ''
        try:
            resp_json = resp.json()
            # with open ('profile.txt', 'w', encoding='utf-8') as f:
            #     f.write(json.dumps(resp_json, indent=4, sort_keys=True))
            # return

        except Exception:
            LOGGING.error('详情接口json内容获取失败')
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_ZIRANKEXUE_PAPER, data=task)

        # 获取标题
        save_data['title'] = self.server.getFieldValue(resp_json, 'chineseTitle')
        # 获取作者
        save_data['zuoZhe'] = self.server.getMoreFieldValue(resp_json, 'authors')
        # 获取成果类型
        productType = int(resp_json['data'][0]['productType'])
        if productType == 3:
            # 成果类型
            save_data['chengGuoLeiXing'] = '会议论文'
            # es ——栏目名称
            save_data['es'] = '会议论文'
            # 获取会议名称
            save_data['huiYiMingCheng'] = self.server.getFieldValue(resp_json, 'journal')
            # 获取语种
            if save_data['huiYiMingCheng']:
                hasChinese = self.server.hasChinese(resp_json, 'journal')
                if hasChinese:
                    save_data['yuZhong'] = "中文"
                else:
                    save_data['yuZhong'] = "英文"
            else:
                save_data['yuZhong'] = ""
        elif productType == 4:
            # 成果类型
            save_data['chengGuoLeiXing'] = '会议论文'
            # es ——栏目名称
            save_data['es'] = '期刊论文'
            # 获取会议名称
            save_data['qiKanMingCheng'] = self.server.getFieldValue(resp_json, 'journal')
            # 获取语种
            if save_data['qiKanMingCheng']:
                hasChinese = self.server.hasChinese(resp_json, 'journal')
                if hasChinese:
                    save_data['yuZhong'] = "中文"
                else:
                    save_data['yuZhong'] = "英文"
            else:
                save_data['yuZhong'] = ""
        # 获取数字对象标识符
        save_data['DOI'] = self.server.getFieldValue(resp_json, 'doi')
        # 获取时间
        shiJian = self.server.getFieldValue(resp_json, 'year')
        if shiJian:
            try:
                save_data['shiJian'] = timeutils.getDateTimeRecord(shiJian)

            except:
                save_data['shiJian'] = shiJian
        else:
            save_data['shiJian'] = ""
        # 获取关键词
        save_data['guanJianCi'] = self.server.getMoreFieldValue(resp_json, 'zhKeyword')
        # 获取摘要
        save_data['zhaiYao'] = self.server.getFieldValue(resp_json, 'zhAbstract')
        # 获取项目类型
        save_data['xinagMuLeiXing'] = self.server.getFieldValue(resp_json, 'supportTypeName')
        # 获取项目编号
        save_data['xinagMuBianHao'] = self.server.getFieldValue(resp_json, 'fundProjectNo')
        # 获取项目名称
        save_data['xinagMuMingCheng'] = self.server.getFieldValue(resp_json, 'fundProject')
        # 获取研究机构
        save_data['yanJiuJiGou'] = self.server.getFieldValue(resp_json, 'organization')
        # 获取点击量
        save_data['dianJiLiang'] = self.server.getFieldValue(resp_json, 'browseCount')
        # 获取下载次数
        save_data['xiaZaiCiShu'] = self.server.getFieldValue(resp_json, 'downloadCount')
        # 获取其它来源网站
        save_data['qiTaLaiYuanWangZhan'] = self.server.getFieldValue(resp_json, 'doiUrl')
        # 获取学科类别
        save_data['xueKeLeiBie'] = self.server.getXueKeLeiBie(resp_json, 'fieldName', xueKeLeiBie)
        # 获取学科领域代码
        save_data['xueKeLingYuDaiMa'] = self.server.getFieldValue(resp_json, 'fieldCode')

        # 获取关联文档
        doc_id = self.server.getFieldValue(resp_json, 'fulltext')
        if doc_id:
            # docu_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperFulltextDownload/' + id
            doc_url = 'http://ir.nsfc.gov.cn/paperDownload/' + doc_id + '.pdf'
            doc_sha = hashlib.sha1(doc_url.encode('utf-8')).hexdigest()
            save_data['guanLianWenDang'] = self.server.guanLianWenDang(doc_url, doc_sha)

            pdf_dict = {}
            pdf_dict['url'] = doc_url
            pdf_dict['sha'] = doc_sha
            pdf_dict['bizTitle'] = save_data['title']
            pdf_dict['relEsse'] = self.server.guanLianLunWen(url, sha)
            # pdf_dict['relPics'] = self.server.guanLianWenDang(doc_url, doc_sha)

            # 存储文档实体及文档本身
            self.document(pdf_dict=pdf_dict, url=url, sha=sha)
        else:
            save_data['guanLianWenDang'] = {}

            # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成ws ——目标网站
        save_data['ws'] = '国家自然科学基金委员会'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_论文'
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
            task_list = self.dao.getTask(key=config.REDIS_ZIRANKEXUE_PAPER, count=1, lockname=config.REDIS_ZIRANKEXUE_PAPER_LOCK)
            # print(task_list)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

                # # 创建gevent协程
                # g_list = []
                # for task in task_list:
                #     s = gevent.spawn(self.run, task)
                #     g_list.append(s)
                # gevent.joinall(g_list)

                # 创建线程池
                threadpool = ThreadPool()
                for url in task_list:
                    threadpool.apply_async(func=self.run, args=(url,))

                threadpool.close()
                threadpool.join()

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
        # main.run(task="{'id': '207d122a-3a68-41b1-8d8a-f20552f22054', 'xueKeLeiBie': '信息科学部', 'url': 'http://ir.nsfc.gov.cn/paperDetail/207d122a-3a68-41b1-8d8a-f20552f22054'}")
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()

    # po = Pool(config.DATA_SCRIPT_PROCESS)
    # for i in range(config.DATA_SCRIPT_PROCESS):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('====== Time consuming is %.2fs ======' %(end_time - begin_time))
