# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import re
import hashlib
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_期刊_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.ZhiWangLunWen_QiKanDataServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化期刊时间列表种子模板
        self.qiKan_time_list_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunLun_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'

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

    def getPaperTask(self, qiKanUrl, qikanSha, xueKeLeiBie):
        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrl, pcode, pykm = self.server.qiKanTimeListUrl(qiKanUrl, self.qiKan_time_list_url_template)
        # 获取期刊时间列表页html源码
        qikanTimeListHtml = self.__getResp(url=qiKanTimeListUrl, mode='get')
        if not qikanTimeListHtml:
            LOGGING.error('期刊时间列表页获取失败, url: {}'.format(qiKanTimeListUrl))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=qikanSha)
            return

        # 获取期刊【年】、【期】列表
        qiKanTimeList = self.server.getQiKanTimeList(qikanTimeListHtml)
        if qiKanTimeList:
            # 循环获取指定年、期页文章列表页种子
            for qikan_year in qiKanTimeList:
                # 获取文章列表页种子
                articleListUrl = self.server.getArticleListUrl(url=self.lunLun_url_template,
                                                               data=qikan_year,
                                                               pcode=pcode,
                                                               pykm=pykm)
                for articleUrl in articleListUrl:
                    # 获取论文列表页html源码
                    article_list_html = self.__getResp(url=articleUrl, mode='get')
                    if not qikanTimeListHtml:
                        LOGGING.error('论文列表页html源码获取失败, url: {}'.format(articleUrl))
                        # 逻辑删除任务
                        self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=qikanSha)
                        return

                    # 获取论文种子列表
                    article_url_list = self.server.getArticleUrlList(article_list_html, qiKanUrl, xueKeLeiBie)
                    if article_url_list:
                        for paper_url in article_url_list:
                            print(paper_url)
                            # 存储种子
                            self.dao.saveTaskToMysql(table=config.MYSQL_PAPER, memo=paper_url, ws='中国知网', es='期刊论文')
                    else:
                        LOGGING.error('论文种子列表获取失败')
        else:
            LOGGING.error('年、期列表获取失败。')


    def handle(self, task, save_data):
        # 获取task数据
        task_data = self.server.getTask(task)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        title = task_data['title']
        xueKeLeiBie = task_data['s_xueKeLeiBie']
        heXinQiKanMuLu = task_data['s_zhongWenHeXinQiKanMuLu']

        # 获取会议主页html源码
        resp = self.__getResp(url=url, mode='get')

        # with open('article.html', 'w', encoding='utf-8') as f:
        #     f.write(article_html.text)

        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
            return

        response = resp.text
        # ========================获取数据==========================
        save_data['title'] = title
        # 获取核心收录
        save_data['heXinShouLu'] = self.server.getHeXinShouLu(response)
        # 获取外文名称
        save_data['yingWenMingCheng'] = self.server.getYingWenMingCheng(response)
        # 获取图片
        save_data['biaoShi'] = self.server.getBiaoShi(response)
        # 获取曾用名
        save_data['cengYongMing'] = self.server.getData(response, '曾用刊名：')
        # 获取主办单位
        save_data['zhuBanDanWei'] = self.server.getData(response, '主办单位：')
        # 获取出版周期
        save_data['chuBanZhouQi'] = self.server.getData(response, '出版周期：')
        # 获取issn
        save_data['ISSN'] = self.server.getData(response, 'ISSN：')
        # 获取CN
        save_data['guoNeiKanHao'] = self.server.getData(response, 'CN：')
        # 获取出版地
        save_data['chuBanDi'] = self.server.getData(response, '出版地：')
        # 获取语种
        # TODO 语种有多值
        save_data['yuZhong'] = self.server.getData(response, '语种：')
        # 获取开本
        save_data['kaiBen'] = self.server.getData(response, '开本：')
        # 获取邮发代号
        save_data['youFaDaiHao'] = self.server.getData(response, '邮发代号：')
        # 获取创刊时间
        shijian = self.server.getData(response, '创刊时间：')
        save_data['shiJian'] = timeutils.getDateTimeRecord(shijian)
        # 获取专辑名称
        save_data['zhuanJiMingCheng'] = self.server.getData2(response, '专辑名称：')
        # 获取专题名称
        save_data['zhuanTiMingCheng'] = self.server.getData2(response, '专题名称：')
        # 获取出版文献量
        try:
            save_data['chuBanWenXianLiang'] = {'v': re.findall(r'\d+', self.server.getData2(response, '出版文献量：'))[0], 'u': '篇'}
        except:
            save_data['chuBanWenXianLiang'] = ""
        # 获取复合影响因子
        save_data['fuHeYingXiangYinZi'] = self.server.getFuHeYingXiangYinZi(response)
        # 获取综合影响因子
        save_data['zongHeYingXiangYinZi'] = self.server.getZongHeYingXiangYinZi(response)
        # 获取来源数据库
        save_data['laiYuanShuJuKu'] = self.server.getLaiYuanShuJuKu(response)
        # 获取期刊荣誉
        save_data['qiKanRongYu'] = self.server.getQiKanRongYu(response)
        # 获取来源分类
        save_data['laiYuanFenLei'] = ""
        # 获取关联主管单位
        save_data['guanLianZhuGuanDanWei'] = {}
        # 获取关联主办单位
        save_data['guanLianZhuBanDanWei'] = {}
        # 生成学科类别
        save_data['xueKeLeiBie'] = xueKeLeiBie
        # 生成核心期刊导航
        save_data['zhongWenHeXinQiKanMuLu'] = heXinQiKanMuLu

        # 保存图片
        if save_data['biaoShi']:
            img_dict = {}
            img_dict['bizTitle'] = save_data['title']
            img_dict['relEsse'] = self.server.guanLianQiKan(url, sha)
            img_dict['relPics'] = {}
            img_url = save_data['biaoShi']
            # # 存储图片种子
            # self.dao.saveProjectUrlToMysql(table=config.MYSQL_IMG, memo=img_dict)
            # 获取图片响应
            media_resp = self.__getResp(url=img_url,
                                        mode='GET')
            if not media_resp:
                LOGGING.error('图片响应失败, url: {}'.format(img_url))
                # 逻辑删除任务
                self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
                return

            img_content = media_resp.content
            # 存储图片
            self.dao.saveMediaToHbase(media_url=img_url, content=img_content, item=img_dict, type='image')

        # =========================== 公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '期刊'
        # 生成es ——栏目名称
        save_data['es'] = '期刊'
        # 生成ws ——目标网站
        save_data['ws'] = '中国知网'
        # 生成clazz ——层级关系
        save_data['clazz'] = '期刊_学术期刊'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_论文'
        # 生成ref
        save_data['ref'] = ''

        # 保存数据到Hbase
        if not save_data:
            LOGGING.info('没有获取数据, 存储失败')
            return
        if 'sha' not in save_data:
            LOGGING.info('数据获取不完整, 存储失败')
            return
        # 存储数据
        success = self.dao.saveDataToHbase(data=save_data)

        # 获取期刊论文种子
        self.getPaperTask(qiKanUrl=url, qikanSha=sha, xueKeLeiBie=xueKeLeiBie)

        return success

    def run(self, task):
        # 创建数据存储字典
        save_data = {}
        # 获取字段值存入字典并返回sha
        success = self.handle(task=task, save_data=save_data)

        if success:
            # 删除任务
            self.dao.deleteTask(table=config.MYSQL_MAGAZINE, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_QIKANLUNWEN_MAGAZINE, count=1, lockname=config.REDIS_QIKANLUNWEN_MAGAZINE_LOCK)
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
        # main.start()
        main.run(task='{"url": "http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JZCK", "title": "计算机测量与控制", "s_xueKeLeiBie": "信息科技_自动化技术", "s_zhongWenHeXinQiKanMuLu": ""}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
