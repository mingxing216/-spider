# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
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
LOGNAME = '期刊_data'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_QiKan(logging=LOGGING)
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
                    LOGGING.error('出现验证码')
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return

    def img(self, img_dict, sha):
        # 获取图片响应
        media_resp = self.__getResp(url=img_dict['url'], method='GET')
        if not media_resp:
            LOGGING.error('图片响应失败, url: {}'.format(img_dict['url']))
            # 标题内容调整格式
            img_dict['bizTitle'] = img_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储图片种子
            self.dao.save_task_to_mysql(table=config.MYSQL_IMG, memo=img_dict, ws='中国知网', es='论文')
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)
            return

        img_content = media_resp.content
        # 存储图片
        succ = self.dao.save_media_to_hbase(media_url=img_dict['url'], content=img_content, item=img_dict, type='image')
        if not succ:
            # 标题内容调整格式
            img_dict['bizTitle'] = img_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # 存储图片种子
            self.dao.save_task_to_mysql(table=config.MYSQL_IMG, memo=img_dict, ws='中国知网', es='论文')
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_MAGAZINE, sha=sha)

    def handle(self, task, save_data):
        # 获取task数据
        task_data = self.server.getEvalResponse(task)
        # print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        xueKeLeiBie = task_data['s_xueKeLeiBie']
        heXinQiKanMuLu = task_data['s_zhongWenHeXinQiKanMuLu']

        # 获取会议主页html源码
        resp = self.__getResp(url=url, method='GET')

        # with open('article.html', 'w', encoding='utf-8') as f:
        #     f.write(resp.text)

        if not resp:
            LOGGING.error('页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
            return

        response = resp.text
        # ========================获取数据==========================
        # 标题
        save_data['title'] = self.server.getTitle(response)
        # 获取核心收录
        save_data['heXinShouLu'] = self.server.getHeXinShouLu(response)
        # 获取外文名称
        save_data['yingWenMingCheng'] = self.server.getYingWenMingCheng(response)
        # 获取图片
        save_data['biaoShi'] = self.server.getBiaoShi(response)
        # 获取曾用名
        save_data['cengYongMing'] = self.server.getData(response, '曾用刊名')
        # 获取主办单位
        save_data['zhuBanDanWei'] = self.server.getMoreData(response, '主办单位')
        # 获取出版周期
        save_data['chuBanZhouQi'] = self.server.getData(response, '出版周期')
        # 获取issn
        save_data['ISSN'] = self.server.getData(response, 'ISSN')
        # 获取CN
        save_data['guoNeiKanHao'] = self.server.getData(response, 'CN')
        # 获取出版地
        save_data['chuBanDi'] = self.server.getData(response, '出版地')
        # 获取语种
        save_data['yuZhong'] = self.server.getData(response, '语种')
        # 获取开本
        save_data['kaiBen'] = self.server.getData(response, '开本')
        # 获取邮发代号
        save_data['youFaDaiHao'] = self.server.getData(response, '邮发代号')
        # 获取创刊时间
        shijian = self.server.getData(response, '创刊时间')
        save_data['chuangKanShiJian'] = timeutils.get_date_time_record(shijian)
        # 获取专辑名称
        save_data['zhuanJiMingCheng'] = self.server.getMoreData(response, '专辑名称')
        # 获取专题名称
        save_data['zhuanTiMingCheng'] = self.server.getMoreData(response, '专题名称')
        # 获取出版文献量
        try:
            save_data['chuBanWenXianLiang'] = {'v': re.findall(r'\d+', self.server.getData(response, '出版文献量'))[0], 'u': '篇'}
        except:
            save_data['chuBanWenXianLiang'] = ""
        # 获取总下载次数
        try:
            save_data['zongXiaZaiCiShu'] = {'v': re.findall(r'\d+', self.server.getData(response, '总下载次数'))[0], 'u': '次'}
        except:
            save_data['zongXiaZaiCiShu'] = ""
        # 获取总被引次数
        try:
            save_data['zongBeiYinCiShu'] = {'v': re.findall(r'\d+', self.server.getData(response, '总被引次数'))[0], 'u': '次'}
        except:
            save_data['zongBeiYinCiShu'] = ""
        # 获取复合影响因子
        save_data['fuHeYingXiangYinZi'] = self.server.getYingXiangYinZi(response, '复合影响因子')
        # 获取综合影响因子
        save_data['zongHeYingXiangYinZi'] = self.server.getYingXiangYinZi(response, '综合影响因子')
        # 获取来源数据库
        save_data['laiYuanShuJuKu'] = self.server.getLaiYuanShuJuKu(response)
        # 获取来源版本
        save_data['laiYuanBanBen'] = self.server.getLaiYuanBanBen(response)
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
            img_dict['url'] = save_data['biaoShi']

            # 存储图片
            self.img(img_dict=img_dict, sha=sha)

        # # 获取期刊论文种子
        # self.getPaperTask(qiKanUrl=url, qikanSha=sha, xueKeLeiBie=xueKeLeiBie)

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
        success = self.dao.save_data_to_hbase(data=save_data)
        if success:
            # 删除任务
            self.dao.delete_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_MAGAZINE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.get_task_from_redis(key=config.REDIS_QIKAN_MAGAZINE, count=50, lockname=config.REDIS_QIKAN_MAGAZINE_LOCK)
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
        # main.run(task='{"url": "http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JSGG", "s_xueKeLeiBie": "经济与管理科学_贸易经济", "s_zhongWenHeXinQiKanMuLu": ""}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
