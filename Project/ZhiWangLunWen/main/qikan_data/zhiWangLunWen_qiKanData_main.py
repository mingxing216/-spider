# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网论文_期刊数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.ZhiWangLunWen_QiKanDataDownloader(logging=LOGGING,
                                                                                         update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                                         proxy_type=config.PROXY_TYPE,
                                                                                         timeout=config.TIMEOUT,
                                                                                         retry=config.RETRY,
                                                                                         proxy_country=config.COUNTRY)
        self.server = service.ZhiWangLunWen_QiKanDataServer(logging=LOGGING)
        self.dao = dao.ZhiWangLunWen_QiKanDataDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 获取task数据
        task = self.server.getTask(task_data)
        sha = task['sha']
        url = task['url']
        # url = 'http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JZCK'
        title = task['title']
        column_name = task['column_name']

        if '|' in column_name:
            xueKeLeiBie = re.findall(r'(.*)\|', column_name)[0]

        else:
            xueKeLeiBie = column_name

        return_data = {}

        # 获取会议主页html源码
        article_html = self.download_middleware.getResp(url=url, mode='get')
        if article_html['status'] == 0:
            article_html = article_html['data'].content.decode('utf-8')
            # ========================获取数据==========================
            return_data['title'] = title
            # 获取核心收录
            return_data['heXinShouLu'] = self.server.getHeXinShouLu(article_html)
            # 获取外文名称
            return_data['yingWenMingCheng'] = self.server.getYingWenMingCheng(article_html)
            # 获取图片
            return_data['biaoShi'] = self.server.getBiaoShi(article_html)
            # 获取曾用名
            return_data['cengYongMing'] = self.server.getData(article_html, '曾用刊名：')
            # 获取主办单位
            return_data['zhuBanDanWei'] = self.server.getData(article_html, '主办单位：')
            # 获取出版周期
            return_data['chuBanZhouQi'] = self.server.getData(article_html, '出版周期：')
            # 获取issn
            return_data['issn'] = self.server.getData(article_html, 'ISSN：')
            # 获取CN
            return_data['guoNeiKanHao'] = self.server.getData(article_html, 'CN：')
            # 获取出版地
            return_data['chuBanDi'] = self.server.getData(article_html, '出版地：')
            # 获取语种
            # TODO 语种有多值
            return_data['yuZhong'] = self.server.getData(article_html, '语种：')
            # 获取开本
            return_data['kaiBen'] = self.server.getData(article_html, '开本：')
            # 获取邮发代号
            return_data['youFaDaiHao'] = self.server.getData(article_html, '邮发代号：')
            # 获取创刊时间
            return_data['shiJian'] = {'Y': self.server.getData(article_html, '创刊时间：')}
            # 获取专辑名称
            return_data['zhuanJiMingCheng'] = self.server.getData2(article_html, '专辑名称：')
            # 获取专题名称
            return_data['zhuanTiMingCheng'] = self.server.getData2(article_html, '专题名称：')
            # 获取出版文献量
            try:
                return_data['chuBanWenXianLiang'] = {'u': '篇',
                                                     'v': re.findall(r'\d+',
                                                                     self.server.getData2(article_html, '出版文献量：'))[0]}
            except:
                return_data['chuBanWenXianLiang'] = {'u': '篇', 'v': 0}
            # 获取复合影响因子
            return_data['fuHeYingXiangYinZi'] = self.server.getFuHeYingXiangYinZi(article_html)
            # 获取综合影响因子
            return_data['zongHeYingXiangYinZi'] = self.server.getZongHeYingXiangYinZi(article_html)
            # 获取来源数据库
            return_data['laiYuanShuJuKu'] = self.server.getLaiYuanShuJuKu(article_html)
            # 获取期刊荣誉
            return_data['qiKanRongYu'] = self.server.getQiKanRongYu(article_html)
            # 获取来源分类
            return_data['laiYuanFenLei'] = ''
            # 获取关联主管单位
            return_data['guanLianZhuGuanDanWei'] = {}
            # 获取关联主办单位
            return_data['guanLianZhuBanDanWei'] = {}
            # 生成学科类别
            return_data['xueKeLeiBie'] = xueKeLeiBie
            # 生成核心期刊导航
            return_data['zhongWenHeXinQiKanMuLu'] = column_name

            # url
            return_data['url'] = url
            # 生成key
            return_data['key'] = url
            # 生成sha
            return_data['sha'] = sha
            # 生成ss ——实体
            return_data['ss'] = '期刊'
            # 生成ws ——目标网站
            return_data['ws'] = '中国知网'
            # 生成clazz ——层级关系
            return_data['clazz'] = '期刊_学术期刊'
            # 生成es ——栏目名称
            return_data['es'] = '学术期刊'
            # 生成biz ——项目
            return_data['biz'] = '文献大数据'
            # 生成ref
            return_data['ref'] = ''

            # --------------------------
            # 存储部分
            # --------------------------
            # 保存媒体url
            if return_data['biaoShi']:
                self.dao.saveMediaToMysql(url=return_data['biaoShi']['url'], type='image')
            # 保存数据
            status = self.dao.saveDataToHbase(data=return_data)
            LOGGING.info(status.content.decode('utf-8'))

        else:
            LOGGING.error('获取文章页html源码失败，url: {}'.format(url))

    def start(self):
        task_list = self.dao.getQiKanUrls()

        if task_list:
            thread_pool = ThreadPool()
            for task in task_list:
                thread_pool.apply_async(func=self.handle, args=(task,))
                # break
            thread_pool.close()
            thread_pool.join()


def process_start():
    main = SpiderMain()
    main.start()


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANGLUNWEN_QIKANDATA_PROCESS_NUMBER)
    for i in range(config.ZHIWANGLUNWEN_QIKANDATA_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
