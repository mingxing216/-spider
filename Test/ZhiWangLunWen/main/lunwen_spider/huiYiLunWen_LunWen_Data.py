# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import hashlib
import re
from scrapy import Selector
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Test.ZhiWangLunWen.middleware import download_middleware
from Test.ZhiWangLunWen.service import service
from Test.ZhiWangLunWen.dao import dao
from Test.ZhiWangLunWen import config
from Utils import timeutils

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<知网_会议论文_data>'  # LOG名
NAME = '知网_会议论文_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False  # 爬虫名入库, 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_LunWenDataServer(logging=LOGGING)
        self.dao = dao.HuiYiLunWen_LunWenDataDao(logging=LOGGING,
                                                 mysqlpool_number=config.MYSQL_POOL_NUMBER,
                                                 redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def __getResp(self, func, url, mode, data=None, cookies=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies)
            if resp['status'] == 0:
                response = resp['data']
                if 'window.location.href' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['status'] == 1:
                return None

    def getLiList(self, i, filename, dbcode, dbname, CurDBCode, page):
        qiKanLunWenIndexUrl = ('http://kns.cnki.net/kcms/detail/frame/list.aspx?'
                               'filename={}'
                               '&dbcode={}'
                               '&dbname={}'
                               '&reftype=1'
                               '&catalogId=lcatalog_CkFiles'
                               '&catalogName='
                               '&CurDBCode={}'
                               '&page={}'.format(filename, dbcode, dbname, CurDBCode, page + 1))
        # 获取该页html
        leiXingResp = self.__getResp(func=self.download_middleware.getResp,
                                     url=qiKanLunWenIndexUrl,
                                     mode='GET')
        if not leiXingResp:
            return []

        leiXingResponse = leiXingResp.text
        leiXingResponseSelector = Selector(text=leiXingResponse)
        leiXingDivList = leiXingResponseSelector.xpath("//div[@class='essayBox']")
        leiXingDiv = leiXingDivList[i]
        li_list = leiXingDiv.xpath(".//li")

        return li_list

    def getGuanLianCanKaoWenXian(self, url):
        return_data = []
        # 获取dbcode
        dbcode = self.server.getDbCode(url=url)
        # 获取filename
        filename = self.server.getFilename(url=url)
        # 获取dbname
        dbname = self.server.getDbname(url=url)
        # 获取参考文献首页url
        canKaoUrl = self.server.getCanKaoWenXianIndexUrl(filename=filename, dbcode=dbcode, dbname=dbname)

        # 获取参考文献页源码
        canKaoResp = self.__getResp(func=self.download_middleware.getResp,
                                    url=canKaoUrl,
                                    mode='GET')
        if not canKaoResp:
            return return_data

        canKaoResponse = canKaoResp.text
        canKapResponseSelector = Selector(text=canKaoResponse)
        div_list = canKapResponseSelector.xpath("//div[@class='essayBox']")
        i = -1
        for div in div_list:
            i += 1
            div1_list = div.xpath("./div[@class='dbTitle']")
            for div1 in div1_list:
                # 获取实体类型
                shiTiLeiXing = div1.xpath("./text()").extract_first()
                if not shiTiLeiXing:
                    continue

                # 获取CurDBCode参数
                span_id = div1.xpath("./b/span/@id").extract_first()
                if not span_id:
                    continue

                try:
                    CurDBCode = re.findall(r"pc_(.*)", span_id)[0]
                except:
                    CurDBCode = None
                if not CurDBCode:
                    continue

                span_text = div1.xpath("./b/span/text()").extract_first()
                if not span_text:
                    continue

                # 获取该类型总页数
                article_number = int(span_text)
                if article_number % 10 == 0:
                    page_number = int(article_number / 10)
                else:
                    page_number = int((article_number / 10)) + 1

                # 题录
                if '题录' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getTiLu(li))

                # 学术期刊
                if '学术期刊' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getXueShuQiKan(li))

                # 国际期刊
                if '国际期刊' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getGuoJiQiKan(li))

                # 图书
                if '图书' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getTuShu(li))

                # 学位
                if '学位' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getXueWei(li))

                # 标准
                if '标准' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getBiaoZhun(li))

                # 专利
                if '专利' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getZhuanLi(li))

                # 报纸
                if '报纸' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getBaoZhi(li))

                # 年鉴
                if '年鉴' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getNianJian(li))

                # 会议
                if '会议' in shiTiLeiXing:
                    # 翻页获取
                    for page in range(page_number):
                        li_list = self.getLiList(i, filename, dbcode, dbname, CurDBCode, page)

                        for li in li_list:
                            return_data.append(self.server.getHuiYi(li))

        return return_data



    def handle(self, task_data):
        save_data = {}
        # 获取task数据
        task = self.server.getTask(task_data)
        url = task['url']
        wenji_url = task['wenji']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # 获取会议主页html源码
        article_resp = self.__getResp(func=self.download_middleware.getResp,
                                      url=url,
                                      mode='GET')
        if not article_resp:
            LOGGING.info('会议主页响应获取失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.deleteLunWenUrl(table=config.LUNWEN_URL_TABLE,
                                     sha=sha)
            return

        article_response = article_resp.text
        # 获取标题
        save_data['title'] = self.server.getArticleTitle(article_response)
        # 获取作者
        save_data['zuoZhe'] = self.server.getZuoZhe(article_response)
        # 获取作者单位
        save_data['faBuDanWei'] = self.server.getFaBuDanWei(article_response)
        # 获取关联企业机构
        save_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_response)
        # 获取摘要
        save_data['zhaiYao'] = self.server.getZhaiYao(article_response)
        # 获取关键词
        save_data['guanJianCi'] = self.server.getGuanJianCi(article_response)
        # 获取会议时间
        save_data['shiJian'] = self.server.getShiJian(article_response)
        # 获取分类号
        save_data['zhongTuFenLeiHao'] = self.server.getZhongTuFenLeiHao(article_response)
        # 获取组图
        '''
        1. 获取组图参数url
        2. 获取组图参数url响应
        3. 获取组图
        '''
        image_data_url = self.server.getImageDataUrl(article_response)
        image_data_resp = self.__getResp(func=self.download_middleware.getResp,
                                         url=image_data_url,
                                         mode='GET')
        if not image_data_resp:
            save_data['zuTu'] = []
        else:
            image_data_response = image_data_resp.text
            save_data['zuTu'] = self.server.getZuTu(image_data_response)
        # 获取下载PDF下载链接
        save_data['xiaZai'] = self.server.getXiaZai(article_response)
        # 获取所在页码
        save_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(article_response)
        # 获取页数
        save_data['yeShu'] = self.server.getYeShu(article_response)
        # 获取大小
        save_data['daXiao'] = self.server.getDaXiao(article_response)
        # 获取论文集url
        lunWenJiDataUrl = self.server.getLunWenJiDataUrl(article_response)
        if not lunWenJiDataUrl:
            save_data['lunWenJi'] = ''
        # 获取论文集
        else:
            lunwenji_resp = self.__getResp(func=self.download_middleware.getResp,
                                           url=lunWenJiDataUrl,
                                           mode='GET')
            if not lunwenji_resp:
                save_data['lunWenJi'] = ''
            else:
                lunwenji_response = lunwenji_resp.text
                save_data['lunWenJi'] = self.server.getLunWenJi(lunwenji_response)
        # 获取下载次数
        save_data['xiaZaiCiShu'] = self.server.getXiaZaiCiShu(article_response)
        # 获取在线阅读地址
        save_data['zaiXianYueDu'] = self.server.getZaiXianYueDu(article_response)
        # 获取关联活动_会议
        save_data['guanLianHuoDong_HuiYi'] = self.server.getGuanLianHuoDong_HuiYi(wenji_url)
        # 获取关联文集
        save_data['guanLianWenJi'] = self.server.getGuanLianWenJi(wenji_url)
        # 获取关联人物
        save_data['guanLianRenWu'] = self.server.getGuanLianRenWu(article_response)
        # 获取参考文献
        save_data['guanLianCanKaoWenXian'] = self.getGuanLianCanKaoWenXian(url=url)
        # 获取关联文档
        save_data['guanLianWenDang'] = {}
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成ws ——目标网站
        save_data['ws'] = '中国知网'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_会议论文'
        # 生成es ——栏目名称
        save_data['es'] = '中国知网_会议论文数据'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''

        # --------------------------
        # 存储部分
        # --------------------------
        # 保存人物队列
        self.dao.saveRenWuToMysql(table=config.ZUOZHE_URL_TABLE,
                                  memo_list=save_data['guanLianRenWu'],
                                  create_at=timeutils.get_now_datetime())
        # 保存机构队列
        self.dao.saveJiGouToMysql(table=config.JIGOU_URL_TABLE,
                                  memo_list=save_data['guanLianQiYeJiGou'],
                                  create_at=timeutils.get_now_datetime())

        # 保存媒体url
        for media in save_data['zuTu']:
            self.dao.save_media_to_mysql(url=media['url'], type='image')

        # 保存数据
        self.dao.save_data_to_hbase(data=save_data)

        # 物理删除任务
        self.dao.deleteUrl(table=config.LUNWEN_URL_TABLE,
                           sha=sha)


    def start(self):
        while True:
            # 从论文队列获取100个论文任务
            task_list = self.dao.getLunWenUrls(key=config.REDIS_HUIYILUNWEN_LUNWEN,
                                               count=100,
                                               lockname=config.REDIS_HUIYILUNWEN_LUNWEN + '_lock')
            if not task_list:
                LOGGING.info('redis无任务')
                time.sleep(10)
                continue

            thread_pool = ThreadPool()
            for task_data in task_list:
                thread_pool.apply_async(func=self.handle, args=(task_data,))
            thread_pool.close()
            thread_pool.join()


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.HUIYI_LUNWEN_SPIDER_PROCESS)
    for i in range(config.HUIYI_LUNWEN_SPIDER_PROCESS):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
