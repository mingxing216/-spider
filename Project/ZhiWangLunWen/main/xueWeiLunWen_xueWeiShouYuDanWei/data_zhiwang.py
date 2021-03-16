# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
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
LOGNAME = '<学位论文_学位授予单位_data>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT)
        self.server = service.XueWeiLunWen_xueWeiShouYuDanWei(logging=LOGGING)
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
            # self.dao.deleteLogicTask(table=config.MYSQL_INSTITUTE, sha=sha)
            return

        img_content = media_resp.content
        # 存储图片
        succ = self.dao.save_media_to_hbase(media_url=img_dict['url'], content=img_content, item=img_dict, type='image')
        if not succ:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_INSTITUTE, sha=sha)

    def handle(self, task, save_data):
        # 数据类型转换
        task_data = self.server.get_eval_response(task)
        # print(task_data)
        url = task_data['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()

        # 获取授予单位详情页html源码
        resp = self.__getResp(url=url, method='GET')
        if not resp:
            LOGGING.error('学位授予单位页面响应失败, url: {}'.format(url))
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_INSTITUTE, sha=sha)
            return

        resp.encoding = resp.apparent_encoding
        article_html = resp.text
        # ========================获取数据==========================
        # 获取标题
        save_data['title'] = self.server.ge_title(article_html)
        # 获取曾用名
        save_data['cengYongMing'] = self.server.get_field(article_html, '曾用名')
        # 获取所在地_内容
        save_data['suoZaiDiNeiRong'] = self.server.get_field(article_html, '地域')
        # 获取主页(官网地址)
        save_data['zhuYe'] = self.server.get_zhu_ye(article_html)
        # 获取标识(图片)
        save_data['biaoShi'] = self.server.get_tu_pian(article_html)
        # 获取标签
        save_data['biaoQian'] = self.server.get_biao_qian(article_html)

        # 保存图片
        if save_data['biaoShi']:
            img_dict = {}
            img_dict['bizTitle'] = save_data['title']
            img_dict['relEsse'] = self.server.guan_lian_dan_wei(url=url, sha=sha)
            img_dict['relPics'] = {}
            img_dict['url'] = save_data['biaoShi']

            self.img(img_dict=img_dict, sha=sha)

        # ======================= 公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = url
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '机构'
        # 生成es ——栏目名称
        save_data['es'] = '学位授予单位'
        # 生成ws ——目标网站
        save_data['ws'] = '中国知网'
        # 生成clazz ——层级关系
        save_data['clazz'] = '机构_学位授予单位'
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
            self.dao.delete_task_from_mysql(table=config.MYSQL_INSTITUTE, sha=sha)
        else:
            # 逻辑删除任务
            self.dao.delete_logic_task_from_mysql(table=config.MYSQL_INSTITUTE, sha=sha)

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.get_task_from_redis(key=config.REDIS_XUEWEI_INSTITUTE, count=30, lockname=config.REDIS_XUEWEI_INSTITUTE_LOCK)
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
        # main.run(task='{"url": "http://navi.cnki.net/knavi/PPaperDetail?pcode=CDMD&logo=GLMWY", "value": "0030"}')
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
