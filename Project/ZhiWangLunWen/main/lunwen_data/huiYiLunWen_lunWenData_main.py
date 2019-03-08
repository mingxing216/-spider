# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import hashlib
import traceback
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<会议论文_论文数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.HuiYiLunWen_LunWenDataDownloader(logging=LOGGING,
                                                                                        update_proxy_frequency=config.UPDATE_PROXY_FREQUENCY,
                                                                                        proxy_type=config.PROXY_TYPE,
                                                                                        timeout=config.TIMEOUT,
                                                                                        retry=config.RETRY,
                                                                                        proxy_country=config.COUNTRY)
        self.server = service.HuiYiLunWen_LunWenDataServer(logging=LOGGING)
        self.dao = dao.HuiYiLunWen_LunWenDataDao(logging=LOGGING)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 获取task数据
        task = self.server.getTask(task_data)
        sha = hashlib.sha1(task['url'].encode('utf-8')).hexdigest()
        return_data = {}
        url = task['url']
        wenji_url = task['wenji']
        # url = 'http://kns.cnki.net/kcms/detail/detail.aspx?sfield=FN&dbcode=CPFD&fileName=JCHX200504001010&tableName=CPFD9908'
        # 查询当前文章是否被抓取过
        status = self.dao.getTaskStatus(sha=sha)

        if status is False:
            # 获取会议主页html源码
            article_html = self.download_middleware.getResp(url=url, mode='get')
            if article_html['status'] == 0:
                # ========================获取数据==========================
                # 获取标题
                return_data['title'] = self.server.getArticleTitle(article_html)
                # 获取作者
                return_data['zuoZhe'] = self.server.getZuoZhe(article_html)
                # 获取作者单位
                return_data['faBuDanWei'] = self.server.getZuoZheDanWei(article_html)
                # 获取关联企业机构
                return_data['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)
                # 获取摘要
                return_data['zhaiYao'] = self.server.getZhaiYao(article_html)
                # 获取关键词
                return_data['guanJianCi'] = self.server.getGuanJianCi(article_html)
                # 获取会议时间
                return_data['shiJian'] = self.server.getShiJian(article_html)
                # 获取分类号
                return_data['zhongTuFenLeiHao'] = self.server.getZhongTuFenLeiHao(article_html)
                # 获取组图
                return_data['zuTu'] = self.server.getZuTo(download_middleware=self.download_middleware,
                                                          resp=article_html)
                # 获取下载PDF下载链接
                return_data['xiaZai'] = self.server.getXiaZai(article_html)
                # 获取所在页码
                return_data['suoZaiYeMa'] = self.server.getSuoZaiYeMa(article_html)
                # 获取页数
                return_data['yeShu'] = self.server.getYeShu(article_html)
                # 获取大小
                return_data['daXiao'] = self.server.getDaXiao(article_html)
                # 获取论文集url
                lunWenJiDataUrl = self.server.getLunWenJiDataUrl(article_html)
                # 获取论文集页响应
                lunwenji_resp = self.download_middleware.getResp(url=lunWenJiDataUrl, mode='get')
                if lunwenji_resp['status'] == 0:
                    # 获取论文集
                    return_data['lunWenJi'] = self.server.getLunWenJi(lunwenji_resp)
                else:
                    LOGGING.error('论文集页获取失败, url: {}'.format(lunWenJiDataUrl))
                    return_data['lunWenJi'] = ''
                # 获取下载次数
                return_data['xiaZaiCiShu'] = self.server.getXiaZaiCiShu(article_html)
                # 获取在线阅读地址
                return_data['zaiXianYueDu'] = self.server.getZaiXianYueDu(article_html)
                # 获取参考文献
                return_data['guanLianCanKaoWenXian'] = self.server.getGuanLianCanKaoWenXian(
                    download_middleware=self.download_middleware,
                    url=url)
                # 获取关联文档
                return_data['guanLianWenDang'] = {}
                # 获取关联活动_会议
                return_data['guanLianHuoDong_HuiYi'] = self.server.getGuanLianHuoDong_HuiYi(wenji_url)
                # 获取关联文集
                return_data['guanLianWenJi'] = self.server.getGuanLianWenJi(wenji_url)
                # 获取关联人物
                return_data['guanLianRenWu'] = self.server.getGuanLianRenWu(article_html)
                # url
                return_data['url'] = url
                # 生成key
                return_data['key'] = url
                # 生成sha
                return_data['sha'] = sha
                # 生成ss ——实体
                return_data['ss'] = '论文'
                # 生成ws ——目标网站
                return_data['ws'] = '中国知网'
                # 生成clazz ——层级关系
                return_data['clazz'] = '论文_会议论文'
                # 生成es ——栏目名称
                return_data['es'] = '中国知网_会议论文数据'
                # 生成biz ——项目
                return_data['biz'] = '文献大数据'
                # 生成ref
                return_data['ref'] = ''

                # --------------------------
                # 存储部分
                # --------------------------
                # 保存人物队列
                self.dao.saveRenWuToMysql(return_data['guanLianRenWu'])
                # 保存机构队列
                self.dao.saveJiGouToMysql(return_data['guanLianQiYeJiGou'])
                # 保存媒体url
                for media in return_data['zuTu']:
                    self.dao.saveMediaToMysql(url=media['url'], type='image')
                # # 记录已抓取任务
                # self.dao.saveComplete(table=config.MYSQL_REMOVAL, sha=sha)
                # 删除任务
                self.dao.deleteLunWenUrl(sha=sha)
                # 保存数据
                status = self.dao.saveDataToHbase(data=return_data)
                LOGGING.info(status)

            else:
                LOGGING.error('获取文章页html源码失败，url: {}'.format(url))
                # 删除任务
                self.dao.deleteLunWenUrl(sha=sha)

        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
            # 删除任务
            self.dao.deleteLunWenUrl(sha=sha)

    def start(self):
        while True:
            # 从论文队列获取100个论文任务
            task_list = self.dao.getLunWenUrls()

            if task_list:
                thread_pool = ThreadPool()
                for task in task_list:
                    thread_pool.apply_async(func=self.handle, args=(task,))
                    # break
                thread_pool.close()
                thread_pool.join()

            else:
                LOGGING.warning('任务队列暂无数据。')
                time.sleep(10)

                continue

            # break


def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    po = Pool(config.HUIYILUNWEN_LUNWENDATA_PROCESS_NUMBER)
    for i in range(config.HUIYILUNWEN_LUNWENDATA_PROCESS_NUMBER):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
