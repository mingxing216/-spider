# -*-coding:utf-8-*-
import sys
import os
import time
import json
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
# 配置文件
import settings
# log日志
from Log import log
# redis连接池
from Utils import redispool_utils
# mysql连接池
from Utils import mysqlpool_utils
# IP工具
# 下载中间件
from Project.WanFangZhuanLi.middleware import download_middleware
# 服务层
from Project.WanFangZhuanLi.services import services
# dao层
from Project.WanFangZhuanLi.dao import dao

log_file_dir = 'WanFangZhuanLi'  # LOG日志存放路径
LOGNAME = '<万方专利老数据抓取程序>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        pass

    def handle(self, redis_client, mysql_client, patent_data):
        patent_data_dict = json.loads(patent_data)
        patent_url = patent_data_dict['url']
        country = patent_data_dict['country']
        save_data = {}
        # 获取专利页html
        index_html = download_middleware.getPatentHtml(logging=LOGGING, redis_client=redis_client, url=patent_url)
        if index_html is not None:
            # 获取标题
            save_data['title'] = services.getTitle(resp=index_html)
            # 获取下载链接
            save_data['xiaZai'] = services.getXiaZai(resp=index_html)
            # 获取在线阅读
            save_data['zaiXianYueDu'] = services.getZaiXianYueDu(resp=index_html)
            # 获取摘要
            save_data['zhaiYao'] = services.getZhaiYao(resp=index_html)
            # 获取专利类型
            save_data['zhuanLiLeiXing'] = services.getZhuanLiLeiXing(resp=index_html)
            # 获取申请号
            save_data['shenQingHao'] = services.getShenQingHao(resp=index_html)
            # 获取申请日
            save_data['shenQingRi'] = services.getShenQingRi(resp=index_html)
            # 获取公开日
            save_data['gongKaiRi'] = services.getGongKaiRi(resp=index_html)
            # 获取公开号
            save_data['gongKaiHao'] = services.getGongKaiHao(resp=index_html)
            # 获取ICP主分类号
            save_data['ipcZhuFenLei'] = services.getIPCZhuFenLei(resp=index_html)
            # 获取IPC分类号
            save_data['ipcFenLeiHao'] = services.getIPCFenLeiHao(resp=index_html)
            # 获取申请人
            save_data['shenQingRen'] = services.getShenQingRen(resp=index_html)
            # 获取发明人
            save_data['faMingRen'] = services.getFaMingRen(resp=index_html)
            # 获取申请人地址
            save_data['shenQingRenDiZhi'] = services.getShenQingRenDiZhi(resp=index_html)
            # 获取代理机构
            save_data['daiLiJiGou'] = services.getDaiLiJiGou(resp=index_html)
            # 获取代理人
            save_data['daiLiRen'] = services.getDaiLiRen(resp=index_html)
            # 获取国省代码
            save_data['guoShengDaiMa'] = services.getGuoShengDaiMa(resp=index_html)
            # 获取主权项
            save_data['zhuQuanXiang'] = services.getZhuQuanXiang(resp=index_html)
            # 获取专利状态
            save_data['zhuanLiZhuangTai'] = services.getZhuanLiZhuangTai(resp=index_html)
            # 专利国别
            save_data['zhuanLiGuoBie'] = country
            # 生成专利url
            save_data['url'] = patent_url
            # 生成sha
            save_data['sha'] = hashlib.sha1(patent_url.encode('utf-8')).hexdigest()
            # 生成key
            save_data['key'] = patent_url
            # 生成ss ——实体
            save_data['ss'] = '专利'
            # 生成ws ——目标网站
            save_data['ws'] = '万方旧版专利数据库'
            # 生成clazz ——层级关系
            save_data['clazz'] = '专利'
            # 生成es ——栏目名称
            save_data['es'] = '专利'
            # 生成biz ——项目
            save_data['biz'] = '文献大数据'
            # 生成ref
            save_data['ref'] = ''

            LOGGING.info(save_data)

            if save_data['title'] == '':
                return

            # 保存数据到hbase
            resp = dao.savePatentDataToHbase_WanFang(logging=LOGGING, data=save_data)
            LOGGING.info(resp)

        # 修改mysql专利状态
        dao.updatePatentDataToMysql(mysql_client=mysql_client, patent_url=patent_url, country=country)


    def processStart(self):
        redis_client = redispool_utils.createRedisPool()
        mysql_client = mysqlpool_utils.createMysqlPool()
        while 1:
            try:
                # 从redis获取100个任务
                patent_urls = set(dao.getPatentUrlForRedis(redis_client=redis_client))
                # # patent_urls = ['{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710954859.X/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710889563.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839228.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710881258.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201810247142.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839605.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710850140.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710879635.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710970174.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710877367.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710942188.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710903751.8/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201810152509.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710911307.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710893739.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710908076.8/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201621139281.X/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201720880006.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710838674.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710886596.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710917479.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710873283.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710514567.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710845540.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710846854.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201820094206.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710914742.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710884698.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710896950.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839265.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839211.8/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201711029014.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201721211627.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710880729.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710943682.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710852438.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710847274.8/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201721709008.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710884888.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710852276.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710859682.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011242561/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839241.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710952267.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710948841.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710941530.X/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011241989/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710744105.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710861884.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710873600.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710946875.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011238206/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710839890.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent//", "country": "\\u7f8e\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710855138.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710956799.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710873100.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710867307.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011244167/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011238639/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710830819.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710903649.8/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710863520.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710995692.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710878890.X/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201810209551.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710861783.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710966054.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710892901.X/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710949918.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710984129.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710860814.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710913711.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710948676.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710944070.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011239271/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201721699553.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011238763/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710848222.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710551072.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710977724.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201810380056.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710944957.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710892129.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710907418.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710860762.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710842567.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201810657667.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710851578.1/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710857018.7/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710869024.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710967506.3/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710872496.5/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710836927.2/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201820016273.9/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201820044835.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710880257.4/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710870924.0/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/CN201710940781.6/", "country": "\\u4e2d\\u56fd\\u4e13\\u5229"}', '{"url": "http://d.old.wanfangdata.com.cn/Patent/JP2011239959/", "country": "\\u65e5\\u672c\\u4e13\\u5229"}']
                if patent_urls:
                    threadpool = ThreadPool(4)
                    for patent_data in patent_urls:
                        threadpool.apply_async(func=self.handle, args=(redis_client, mysql_client, patent_data))
                        # break
                    threadpool.close()
                    threadpool.join()
                    continue
                else:
                    LOGGING.info('redis队列暂无任务')
                    time.sleep(10)
                    continue

                # break
            except Exception as e:
                LOGGING.error('发生错误: {}'.format(e))
                continue

    def run(self):
        # self.processStart()
        po = Pool(settings.WANFANG_PATENT_DATA_SPIDER_PROCESS)
        for p in range(settings.WANFANG_PATENT_DATA_SPIDER_PROCESS):
            po.apply_async(func=self.processStart)
        po.close()
        po.join()


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
