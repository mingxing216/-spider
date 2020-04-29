# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import traceback
import ast
import copy
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config
from Utils import timeutils

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<期刊论文_论文_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                 proxy_type=config.PROXY_TYPE,
                                                                 timeout=config.TIMEOUT)
        self.server = service.LunWen_Data(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_MAX_NUMBER,
                           redispool_number=config.REDIS_POOL_MAX_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def imgDownload(self, img_task):
        # 获取图片响应
        media_resp = self.__getResp(url=img_task['img_dict']['url'], method='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_task['img_dict']['url']))
            # 标题内容调整格式
            img_task['img_dict']['bizTitle'] = img_task['img_dict']['bizTitle'].replace('"', '\\"').replace("'", "''")
            # 存储图片种子
            self.dao.saveTaskToMysql(table=config.MYSQL_IMG, memo=img_task['img_dict'], ws='中国知网', es='论文')

            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=img_task['sha'])
            return
        media_resp.encoding = media_resp.apparent_encoding
        img_content = media_resp.content
        # 存储图片
        succ = self.dao.saveMediaToHbase(media_url=img_task['img_dict']['url'], content=img_content, item=img_task['img_dict'],
                                         type='image')
        if not succ:
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=img_task['sha'])
            # 标题内容调整格式
            img_task['img_dict']['bizTitle'] = img_task['img_dict']['bizTitle'].replace('"', '\\"').replace("'", "''")
            # 存储图片种子
            self.dao.saveTaskToMysql(table=config.MYSQL_IMG, memo=img_task['img_dict'], ws='中国知网', es='论文')
            return

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.getEvalResponse(task)
        # print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # # 查询当前文章是否被抓取过
        # status = self.dao.getTaskStatus(sha=sha)

        # 获取论文主页html源码
        resp = self.__getResp(url=url, method='GET')
        if not resp:
            LOGGING.error('会议论文详情页响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            return

        resp.encoding = resp.apparent_encoding
        article_html = resp.text

        # 获取标题
        save_data['title'] = self.server.getTitle(article_html)
        # 获取作者
        save_data['zuoZhe'] = self.server.getZuoZhe(article_html)
        # 获取作者单位
        save_data['zuoZheDanWei'] = self.server.getZuoZheDanWei(article_html)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(article_html)
        # 获取关键词
        save_data['guanJianCi'] = self.server.getMoreFields(article_html, '关键词')
        # 获取基金
        save_data['jiJin'] = self.server.getMoreFields(article_html, '基金')
        # 数字对象标识符
        save_data['DOI'] = self.server.getMoreFields(article_html, 'DOI')
        # 获取中图分类号
        save_data['zhongTuFenLeiHao'] = self.server.getMoreFields(article_html, '分类号')
        # 期刊名称
        save_data['qiKanMingCheng'] = self.server.getQiKanName(article_html)
        # 期号
        save_data['qiHao'] = self.server.getQiHao(article_html)
        # 获取下载
        save_data['xiaZai'] = task_data.get('xiaZai')
        # 获取在线阅读
        save_data['zaiXianYueDu'] = task_data.get('zaiXianYueDu')
        # 获取下载次数
        save_data['xiaZaiCiShu'] = self.server.getXiaZai(article_html)
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(article_html)
        # 获取页数
        save_data['yeShu'] = self.server.getYeShu(article_html)
        # 获取大小
        save_data['daXiao'] = self.server.getDaXiao(article_html)
        # 获取时间
        shijian = self.server.getYear(article_html)
        if shijian:
            save_data['shiJian'] = timeutils.getDateTimeRecord(shijian)
        else:
            save_data['shiJian'] = ''
        # 学科类别
        save_data['xueKeLeiBie'] = task_data.get('xueKeLeiBie')
        # 来源分类
        save_data['laiYuanFenLei'] = ''
        # 获取参考文献
        save_data['guanLianCanKaoWenXian'] = self.server.canKaoWenXian(url=url, download=self.__getResp)
        # 关联期刊
        save_data['guanLianQiKan'] = self.server.guanLianQiKan(task_data.get('parentUrl'))
        # 关联人物
        save_data['guanLianRenWu'] = self.server.guanLianRenWu(article_html)
        # 关联企业机构
        save_data['guanLianQiYeJiGou'] = self.server.guanLianQiYeJiGou(article_html)
        # 关联文档
        save_data['guanLianWenDang'] = {}

        # 获取所有图片链接
        picDatas = self.server.getPicUrl(resp=article_html, fetch=self.__getResp)
        if picDatas:
            # 获取组图(关联组图)
            save_data['relationPics'] = self.server.guanLianPics(url, sha)
            # 组图实体
            pics = {}
            # 标题
            pics['title'] = save_data['title']
            # 组图内容
            pics['labelObj'] = self.server.getPics(picDatas)
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
            pics['es'] = '期刊论文'
            # 生成ws ——目标网站
            pics['ws'] = '中国知网'
            # 生成clazz ——层级关系
            pics['clazz'] = '组图_实体'
            # 生成biz ——项目
            pics['biz'] = '文献大数据_论文'
            # 生成ref
            pics['ref'] = ''
            # 保存组图实体到Hbase
            self.dao.saveDataToHbase(data=pics)

            # 创建图片任务列表
            img_tasks = []

            # 下载图片
            for img in picDatas:
                dict = {}
                dict['sha'] = sha
                dict['img_dict'] = {}
                dict['img_dict']['url'] = img['url']
                dict['img_dict']['bizTitle'] = img['title']
                dict['img_dict']['relEsse'] = self.server.guanLianLunWen(url, sha)
                dict['img_dict']['relPics'] = self.server.guanLianPics(url, sha)
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
            # 获取组图(关联组图)
            save_data['relationPics'] = {}

        # ====================================公共字段
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
        save_data['biz'] = '文献大数据_论文'
        # 生成ref
        save_data['ref'] = ''

        # --------------------------
        # 存储部分
        # --------------------------
        # 保存人物队列
        people_list = self.server.getPeople(zuozhe=save_data['guanLianRenWu'], daoshi=save_data.get('guanLianDaoShi'), t=save_data['shiJian'])
        # print(people_list)
        if people_list:
            for people in people_list:
                self.dao.saveTaskToMysql(table=config.MYSQL_PEOPLE, memo=people, ws='中国知网', es='论文')
        # 保存机构队列
        if save_data['guanLianQiYeJiGou']:
            for jigou  in save_data['guanLianQiYeJiGou']:
                self.dao.saveTaskToMysql(table=config.MYSQL_INSTITUTE, memo=jigou, ws='中国知网', es='论文')

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
            task_list = self.dao.getTask(key=config.REDIS_QIKAN_PAPER, count=20, lockname=config.REDIS_QIKAN_PAPER_LOCK)
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

                # # 创建线程池
                # threadpool = ThreadPool()
                # for url in task_list:
                #     threadpool.apply_async(func=self.run, args=(url,))
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
        # main.run('{"url": "http://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=KYGL2017S1059&dbname=CJFDLAST2017", "xiaZai": "http://navi.cnki.net/knavi/Common/RedirectPage?sfield=XZ&q=rqbwtGUZJ7kGEDCwAni8wGOGuEv0N4vz%mmd2BiQ8as210mgQvjcNzI7jHsUpk0WIr%mmd2B0y&tableName=CJFDLAST2017", "zaiXianYueDu": "http://navi.cnki.net/knavi/Common/RedirectPage?sfield=RD&dbCode=CJFD&filename=KYGL2017S1059&tablename=CJFDLAST2017&filetype=XML;EPUB;", "xueKeLeiBie": "基础科学_基础科学综合", "parentUrl": "http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=KYGL"}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()

    # po = Pool(1)
    # for i in range(1):
    #     po.apply_async(func=process_start)
    # po.close()
    # po.join()

    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))