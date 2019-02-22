# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import multiprocessing
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWangPapers.middleware import download_middleware
from Project.ZhiWangPapers.service import service
from Project.ZhiWangPapers.dao import dao
from Project.ZhiWangPapers import config

log_file_dir = 'ZhiWangPapers'  # LOG日志存放路径
LOGNAME = '<知网期刊论文数据爬虫>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.LunWenDownloader(logging=LOGGING,
                                                                  update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  retry=config.RETRY,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.LunWenServer(logging=LOGGING)
        self.dao = dao.LunWenDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化机构redis集合名
        self.qikanjigou = 'qikanjigou'
        # 初始化mysql数据库论文任务去重表
        self.lunwen_table = 'ss_paper'
        # 初始化mysql数据库论文任务表名
        self.lunwen_url_table = 'ss_paper_url'

    def handle(self, article_url_data):
        sha = article_url_data['sha']
        datas = json.loads(article_url_data['memo'])
        return_data = {}
        # url = datas['url']
        url = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbCode=CJFD&filename=ZGTL201306005&tableName=CJFD2013'
        # 查询当前文章是否被抓取过
        status = self.dao.getLunWenStatus(table=self.lunwen_table, sha=sha)

        if status is False:
            urldata_qiKanUrl = datas['qiKanUrl']
            # 获取文章页html源码
            article_html = self.download_middleware.getResp(url=url)
            if article_html['status'] == 0:
                # ========================获取数据==========================
                # 获取期刊名称
                return_data['qiKanMingCheng'] = self.server.getQiKanMingCheng(article_html)
                # 获取关联文档
                return_data['guanLianWenDang'] = {}
                # 获取参考文献
                return_data['guanLianCanKaoWenXian'] = self.server.getGuanLianCanKaoWenXian(download_middleware=self.download_middleware,
                                                                                            url=url)
                # 获取文章种子sha1加密
                return_data['sha'] = sha
                # 获取时间【年】
                return_data['shiJian'] = self.server.getshiJian(article_html)
                # 获取页数
                return_data['yeShu'] = self.server.getYeShu(article_html)
                # 获取关联图书期刊
                return_data['guanLianTuShuQiKan'] = self.server.getGuanLianTuShuQiKan(urldata_qiKanUrl)
                # 获取作者
                return_data['zuoZhe'] = self.server.getZuoZhe(article_html)
                # 获取文章标题
                return_data['title'] = self.server.getArticleTitle(article_html)
                # 获取关联企业机构
                return_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)
                # 获取下载PDF下载链接
                return_data['xiaZai'] = self.server.getXiaZai(article_html)
                # 类别
                return_data['ss'] = '论文'
                # 获取关键词
                return_data['guanJianCi'] = self.server.getGuanJianCi(article_html)
                # 获取作者单位
                return_data['faBuDanWei'] = self.server.getZuoZheDanWei(article_html)
                # 生成key字段
                return_data['key'] = url
                # 获取大小
                return_data['daXiao'] = self.server.getDaXiao(article_html)
                # 获取在线阅读地址
                return_data['zaiXianYueDu'] = self.server.getZaiXianYueDu(article_html)
                # 获取分类号
                return_data['zhongTuFenLeiHao'] = self.server.getZhongTuFenLeiHao(article_html)
                # 获取下载次数
                return_data['xiaZaiCiShu'] = self.server.getXiaZaiCiShu(article_html)
                # 生成ws字段
                return_data['ws'] = '中国知网'
                # 生成url字段
                return_data['url'] = url
                # 生成biz字段
                return_data['biz'] = '文献大数据'
                # 生成ref字段
                return_data['ref'] = url
                # 获取期号
                return_data['qiHao'] = self.server.getQiHao(article_html)
                # 获取所在页码
                return_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(article_html)
                # 获取摘要
                return_data['zhaiYao'] = self.server.getZhaiYao(article_html)
                # 生成es字段
                return_data['ex'] = '期刊论文'
                # 生成clazz字段
                return_data['clazz'] = '论文_期刊论文'
                # 获取基金
                return_data['jiJin'] = self.server.getJiJin(article_html)
                # 获取文内图片
                return_data['wenNeiTuPian'] = self.server.getWenNeiTuPian(download_middleware=self.download_middleware,
                                                                          url=url,
                                                                          resp=article_html)
                if return_data['wenNeiTuPian']:
                    for image_data in return_data['wenNeiTuPian']:
                        self.dao.saveMediaToMysql(url=image_data['image_url'], type='image')

                # 获取doi
                return_data['shuZiDuiXiangBiaoShiFu'] = self.server.getDoi(article_html)
                # 生成来源分类字段
                return_data['laiYuanFenLei'] = ''
                # 生成学科类别分类
                return_data['xueKeLeiBie'] = datas['xueKeLeiBie']
                # 获取关联人物
                guanLianRenWu_Data = self.server.getGuanLianRenWu(download_middleware=self.download_middleware,
                                                                  resp=article_html,
                                                                  year=return_data['shiJian'])
                return_data['guanLianRenWu'] = []
                for man in guanLianRenWu_Data:
                    data = {}
                    data['sha'] = man['sha']
                    data['ss'] = '人物'
                    data['url'] = man['url']
                    data['name'] = man['name']
                    return_data['guanLianRenWu'].append(data)

                # # 生成关联人物url队列
                # for man_url in return_data["guanLianRenWu"]:
                #     url = man_url['url']
                #     redispool_utils.sadd(redis_client=redis_client, key='qikanrenwu', value=url)

                # 生成关联企业机构url队列
                for jiGou in return_data["guanLianQiYeJiGou"]:
                    url = jiGou['url']
                    self.dao.saveJiGouToRedis(key=self.qikanjigou, value=url)

                # 生成关联人物表数据入库
                for renWuData in guanLianRenWu_Data:
                    insert_renwu_data = {}
                    try:
                        insert_renwu_data['ref'] = renWuData['url']
                    except:
                        insert_renwu_data['ref'] = ''
                    try:
                        insert_renwu_data['title'] = renWuData['name']
                    except:
                        insert_renwu_data['title'] = ''
                    try:
                        insert_renwu_data['guanLianQiYeJiGou'] = [{"sha": renWuData['suoZaiDanWei']['单位sha1'],
                                                                   "ss": "机构",
                                                                   "url": renWuData['suoZaiDanWei']['单位url'], }]
                    except:
                        insert_renwu_data['guanLianQiYeJiGou'] = []
                    try:
                        insert_renwu_data['sha'] = renWuData['sha']
                    except:
                        insert_renwu_data['sha'] = ''
                    try:
                        insert_renwu_data['suoZaiDanWei'] = [{"所在单位": renWuData["suoZaiDanWei"]['所在单位'],
                                                              "时间": renWuData['suoZaiDanWei']['时间']}]
                    except:
                        insert_renwu_data['suoZaiDanWei'] = []
                    insert_renwu_data['ss'] = '人物'
                    insert_renwu_data['ws'] = '中国知网'
                    insert_renwu_data['clazz'] = '人物_论文作者'
                    insert_renwu_data['es'] = '期刊论文'
                    try:
                        insert_renwu_data['key'] = renWuData['url']
                    except:
                        insert_renwu_data['key'] = ''
                    try:
                        insert_renwu_data['url'] = renWuData['url']
                    except:
                        insert_renwu_data['url'] = ''
                    insert_renwu_data['biz'] = '文献大数据'

                    # 存入关联人物数据库
                    self.dao.saveDataToHbase(data=insert_renwu_data)

                # 存储sha到mysql
                self.dao.saveLunWenSha(table=self.lunwen_table, sha=sha)
                # 删除任务
                self.dao.deleteLunWenUrl(table=self.lunwen_url_table, sha=sha)
                status = self.dao.saveDataToHbase(data=return_data)
                LOGGING.info(status.content.decode('utf-8'))

            else:
                LOGGING.error('获取文章页html源码失败，url: {}'.format(url))

        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
            # 删除任务
            self.dao.deleteLunWenUrl(table=self.lunwen_url_table, sha=sha)

    def start(self):
        while True:
            # 从论文队列获取100个论文任务
            datas = self.dao.getLunWenUrls(table=self.lunwen_url_table)

            if datas:
                thread_pool = ThreadPool()
                for article_url_data in datas:
                    thread_pool.apply_async(func=self.handle, args=(article_url_data, ))
                    # break
                thread_pool.close()
                thread_pool.join()

            else:
                time.sleep(10)

                continue

            # break


def start():
    main = SpiderMain()
    main.start()

if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.ZHIWANG_PERIODOCAL_SPIDER_PROCESS)
    for i in range(config.ZHIWANG_PERIODOCAL_SPIDER_PROCESS):
        po.apply_async(func=start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
