# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import multiprocessing
import re
import hashlib
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangPapers.middleware import download_middleware
from Project.ZhiWangPapers.service import service
from Project.ZhiWangPapers.dao import dao
from Project.ZhiWangPapers import config

log_file_dir = 'ZhiWangPapers'  # LOG日志存放路径
LOGNAME = '<知网文献关联期刊爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.QiKanDownloader(logging=LOGGING,
                                                                       update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                       proxy_type=config.PROXY_TYPE,
                                                                       timeout=config.TIMEOUT,
                                                                       retry=config.RETRY,
                                                                       proxy_country=config.COUNTRY)
        self.server = service.QiKanServer(logging=LOGGING)
        self.dao = dao.QiKanDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 第一个期刊集合数据
        self.first_data = []
        # 最后一个期刊集合数据
        self.last_data = []
        # 期刊总集合
        self.data = []
        # 期刊总集合2
        self.data2 = []
        # 期刊队列
        manager = multiprocessing.Manager()
        self.url_q = manager.Queue()

        self.url_data = []

    def itegrationOfData(self):
        '''整合redis队列数据'''

        # 获取第一个栏目集合数据
        datas_1 = self.dao.getData1()
        for data1 in datas_1:
            self.first_data.append(json.loads(data1))

        # 获取最后一个栏目集合数据
        datas_2 = self.dao.getData2()
        for data2 in datas_2:
            self.last_data.append(json.loads(data2))

        for first_data in self.first_data:
            # 获取总集合内元素数量
            data_number = len(self.data)
            first_column_name = first_data['column_name']
            first_url = first_data['url']

            for last_data in self.last_data:
                last_column_name = last_data['column_name']
                last_url = last_data['url']

                if last_url == first_url:
                    name = first_column_name + '|' + last_column_name
                    first_data['column_name'] = name
                    self.data.append(first_data)

            # 获取总集合内元素数量
            data_number_two = len(self.data)
            if data_number == data_number_two:
                self.data.append(first_data)
                continue
            else:

                continue

        # 生成任务队列
        for data in self.data:
            self.url_q.put(data)
        LOGGING.info('队列已生成， 任务数量: {}'.format(self.url_q.qsize()))

    def handel(self,url_data):
        # url_data = {'column_name': '社会科学II_初等教育', 'title': '第二课堂(C)', 'url': 'http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=JZCK'}
        return_data = {}
        url = url_data['url']
        column_name = url_data['column_name']

        if '|' in column_name:
            xueKeLeiBie = re.findall(r'(.*)\|', column_name)[0]
            heXinQiKanDaoHang = column_name
        else:
            xueKeLeiBie = column_name
            heXinQiKanDaoHang = ''

        # 获取期刊页html源码
        resp = self.download_middleware.getResp(url=url)
        # 获取标题
        return_data['title'] = self.server.getTitle(resp)
        # 获取核心收录
        return_data['heXinShouLu'] = self.server.getHeXinShouLu(resp)
        # 获取外文名称
        return_data['yingWenMingCheng'] = self.server.getYingWenMingCheng(resp)
        # 获取图片
        return_data['biaoShi'] = self.server.getBiaoShi(resp)
        # 获取曾用名
        return_data['cengYongMing'] = self.server.getData(resp, '曾用刊名：')
        # 获取主办单位
        return_data['zhuBanDanWei'] = self.server.getData(resp, '主办单位：')
        # 获取出版周期
        return_data['chuBanZhouQi'] = self.server.getData(resp, '出版周期：')
        # 获取issn
        return_data['issn'] = self.server.getData(resp, 'ISSN：')
        # 获取CN
        return_data['guoNeiKanHao'] = self.server.getData(resp, 'CN：')
        # 获取出版地
        return_data['chuBanDi'] = self.server.getData(resp, '出版地：')
        # 获取语种
        # TODO 语种有多值
        return_data['yuZhong'] = self.server.getData(resp, '语种：')
        # 获取开本
        return_data['kaiBen'] = self.server.getData(resp, '开本：')
        # 获取邮发代号
        return_data['youFaDaiHao'] = self.server.getData(resp, '邮发代号：')
        # 获取创刊时间
        return_data['shiJian'] = {'Y': self.server.getData(resp, '创刊时间：')}
        # 获取专辑名称
        return_data['zhuanJiMingCheng'] = self.server.getData2(resp, '专辑名称：')
        # 获取专题名称
        return_data['zhuanTiMingCheng'] = self.server.getData2(resp, '专题名称：')
        # 获取出版文献量
        try:
            return_data['chuBanWenXianLiang'] = {'u': '篇', 'v': re.findall(r'\d+', self.server.getData2(resp, '出版文献量：'))[0]}
        except:
            return_data['chuBanWenXianLiang'] = {'u': '篇', 'v': 0}
        # 获取复合影响因子
        return_data['fuHeYingXiangYinZi'] = self.server.getFuHeYingXiangYinZi(resp)
        # 获取综合影响因子
        return_data['zongHeYingXiangYinZi'] = self.server.getZongHeYingXiangYinZi(resp)
        # 获取来源数据库
        return_data['laiYuanShuJuKu'] = self.server.getLaiYuanShuJuKu(resp)
        # 获取期刊荣誉
        return_data['qiKanRongYu'] = self.server.getQiKanRongYu(resp)
        # 获取来源分类
        return_data['laiYuanFenLei'] = ''
        # 获取关联主管单位
        return_data['guanLianZhuGuanDanWei'] = {}
        # 获取关联主办单位
        return_data['guanLianZhuBanDanWei'] = {}
        # 生成学科类别
        return_data['xueKeLeiBie'] = xueKeLeiBie
        # 生成核心期刊导航
        return_data['heXinQiKanDaoHang'] = heXinQiKanDaoHang

        # url
        return_data['url'] = url
        # 生成key
        return_data['key'] = url
        # 生成sha
        return_data['sha'] = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 生成ss ——实体
        return_data['ss'] = '期刊'
        # 生成ws ——目标网站
        return_data['ws'] = '中国知网'
        # 生成clazz ——层级关系
        return_data['clazz'] = '期刊_学术期刊'
        # 生成es ——栏目名称
        return_data['es'] = '期刊'
        # 生成biz ——项目
        return_data['biz'] = '文献大数据'
        # 生成ref
        return_data['ref'] = ''

        # 数据入库
        save_data_status = self.dao.saveDataToHbase(data=return_data).content.decode('utf-8')

        LOGGING.info('数据存储状态: {}, url: {}'.format(save_data_status, url))

        # 保存图片url
        self.dao.saveMediaToMysql(url=return_data['biaoShi'], type='image')


    def spider_run(self, url_datas):
        po = ThreadPool()
        for url_data in url_datas:
            po.apply_async(func=self.handel, args=(url_data,))

        po.close()
        po.join()

    def start(self):
        while True:
            # 获取机构任务(100个)
            url_datas = []
            for i in range(100):
                if self.url_q.qsize() == 0:
                    break
                else:
                    try:
                        url_data = self.url_q.get_nowait()
                    except:
                        url_data = None
                    if url_data:
                        url_datas.append(url_data)

            if not url_datas:
                break
            if url_datas:
                LOGGING.info(self.url_q.qsize())
                self.spider_run(url_datas=url_datas)
            else:
                LOGGING.error('期刊队列任务结束')
                break



if __name__ == '__main__':
    main = SpiderMain()
    main.itegrationOfData()
    main.start()
    # main.handel(1)
