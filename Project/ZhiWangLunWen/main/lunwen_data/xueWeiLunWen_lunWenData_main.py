# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import ast
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<学位论文_论文数据>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.XueWeiLunWen_LunWenDataDownloader(logging=LOGGING,
                                                                                         proxy_type=config.PROXY_TYPE,
                                                                                         timeout=config.TIMEOUT,
                                                                                         proxy_country=config.COUNTRY)
        self.server = service.XueWeiLunWen_LunWenDataServer(logging=LOGGING)
        self.dao = dao.XueWeiLunWen_LunWenDataDao(logging=LOGGING, mysqlpool_number=5, redispool_number=5)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def handle(self, task_data):
        # 将任务数据转换成python字典类型，redis返回的是str格式
        task_data_dict = ast.literal_eval(task_data)

        # 获取数据主键
        sha = task_data_dict['sha']
        # 获取task数据
        task = self.server.getTask(task_data_dict)

        if task is None:
            # 数据有异常, 从mysql数据库删除本数据, 并退出当前任务
            self.dao.deleteLunWenUrl(sha=sha)
            return

        # # task = {'title': '高强水泥基复合材料雷达波吸收性能研究', 'zuoZhe': '国爱丽', 'daoShiXingMing': '巴恒静', 'xiaZaiCiShu': '808',
        # #         'shiJian': '2010', 'xueWeiLeiXing': '博士', 'zhuanYe': '工学_土木工程_结构工程',
        # #         'url': 'http://kns.cnki.net/kcms/detail/detail.aspx?sfield=FN&dbCode=CDFD&fileName=2011015993.nh&tableName=CDFD0911'}
        url = task['url']

        # 查询当前文章是否被抓取过
        status = self.dao.getTaskStatus(sha=sha)

        # False说明没有被抓取过
        if status is False:

            # 获取论文主页html源码
            article_html = self.download_middleware.getResp(url=url, mode='get')

            # 判断响应状态
            if article_html['status'] == 0:
                article_html = article_html['data'].content.decode('utf-8')

                # 获取发布单位
                task['faBuDanWei'] = self.server.getFaBuDanWei(article_html)
                # 获取摘要
                task['zhaiYao'] = self.server.getZhaiYao(article_html)
                # 获取关键词
                task['guanJianCi'] = self.server.getGuanJianCi(article_html)
                # 获取基金
                task['jiJin'] = self.server.getJiJin(article_html)
                # 获取分类号
                task['zhongTuFenLeiHao'] = self.server.getZhongTuFenLeiHao(article_html)
                # 获取文内图片
                task['zuTu'] = self.server.getZuTo(download_middleware=self.download_middleware,
                                                   resp=article_html)
                # 获取页数
                task['yeShu'] = self.server.getYeShu(article_html)
                # 获取大小
                task['daXiao'] = self.server.getDaXiao(article_html)
                # 获取下载
                task['xiaZai'] = self.server.getXiaZai(article_html)
                # 获取在线阅读
                task['zaiXianYueDu'] = self.server.getZaiXianYueDu(article_html)
                # 获取参考文献
                task['guanLianCanKaoWenXian'] = self.server.getGuanLianCanKaoWenXian(
                    download_middleware=self.download_middleware,
                    url=url)
                # 获取关联人物
                task['guanLianRenWu'] = self.server.getGuanLianRenWu(article_html)
                # 获取关联导师
                task['guanLianDaoShi'] = self.server.getGuanLianDaoShi(article_html)
                # 获取关联企业机构
                task['guanLianQiYeJiGou'] = self.server.getGuanLianQiYeJiGou(article_html)
                # 获取关联文档
                task['guanLianWenDang'] = ''

                # 生成key
                task['key'] = url
                # 生成sha
                task['sha'] = sha
                # 生成ss ——实体
                task['ss'] = '论文'
                # 生成ws ——目标网站
                task['ws'] = '中国知网'
                # 生成clazz ——层级关系
                task['clazz'] = '论文_学位论文'
                # 生成es ——栏目名称
                task['es'] = '中国知网_学位论文数据'
                # 生成biz ——项目
                task['biz'] = '文献大数据'
                # 生成ref
                task['ref'] = ''

                # --------------------------
                # 存储部分
                # --------------------------
                # 保存人物队列
                self.dao.saveRenWuToMysql(task['guanLianRenWu'])
                # 保存机构队列
                self.dao.saveJiGouToMysql(task['guanLianQiYeJiGou'])
                # 保存媒体url
                for media in task['zuTu']:
                    self.dao.saveMediaToMysql(url=media['url'], type='image')
                # # 记录已抓取任务
                # self.dao.saveComplete(table=config.MYSQL_REMOVAL, sha=sha)

                # 保存数据
                status = ast.literal_eval(self.dao.saveDataToHbase(data=task))
                if str(status['resultCode']) == '0':
                    self.dao.deleteLunWenUrl(sha=sha)

                LOGGING.warning(str(status))

            else:
                LOGGING.error('获取论文页html源码失败，url: {}'.format(url))
                self.dao.deleteLunWenUrl(sha=sha)
        else:
            LOGGING.warning('{}: 已被抓取过'.format(sha))
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
    po = Pool(config.XUEWEILUNWEN_LUNWENDATA_PROCESS_NUMBER)
    for i in range(config.XUEWEILUNWEN_LUNWENDATA_PROCESS_NUMBER):
    # po = Pool(1)
    # for i in range(1):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
