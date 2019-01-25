# -*-coding:utf-8-*-

'''
专利摘要爬虫
'''
import sys
import os
import time
import json
import hashlib
import pprint

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Utils import redispool_utils
from Utils import mysqlpool_utils
from Utils import user_agent_u
from Project.DaWeiSpiderProject.services import services
from Project.DaWeiSpiderProject.middleware import download_middleware
from Project.DaWeiSpiderProject.dao import dao
from Project.DaWeiSpiderProject.main import register

log_file_dir = 'DaWeiSpiderProject'  # LOG日志存放路径
LOGNAME = '<大为专利种子抓取>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class SpiderMain(object):
    def __init__(self):
        self.index_url = 'http://www.innojoy.com/client/interface.aspx' # post请求url
        # 专利分类列表
        # self.patent_type_list = ["A%", "B%", "C%", "D%", "E%", "F%", "G%", "H%"]
        self.patent_type_list = ["G%"]
        # 地区分类列表
        self.add_list = ['fmzl', 'syxx', 'wgzl', 'fmsq', 'twpat', 'hkpat', 'fmsq', 'wgzl', 'syxx', 'fmzl', 'usapp',
                         'uspat', 'uspat1', 'usdes', 'epapp', 'eppat', 'wopat', 'jpapp', 'jppat', 'jputi', 'krapp',
                         'krpat', 'kruti', 'deapp', 'depat', 'deuti', 'rupat', 'gbpat', 'frpat', 'chpat', 'ispat',
                         'dkpat', 'grpat', 'czpat', 'nopat', 'fipat', 'nlpat', 'plpat', 'sepat', 'iepat', 'bepat',
                         'hupat', 'itpat', 'espat', 'uapat', 'uypat', 'atpat', 'ptpat', 'mtpat', 'mcpat', 'lupat',
                         'ltpat', 'supat', 'yupat', 'skpat', 'smpat', 'ropat', 'rspat', 'mdpat', 'lvpat', 'hrpat',
                         'gepat', 'eepat', 'cypat', 'bgpat', 'bypat', 'sipat', 'mepat', 'eapat', 'cspat', 'ddpat',
                         'bapat', 'inpat', 'inapp', 'jopat', 'vnpat', 'thpat', 'mnpat', 'ilpat', 'sgpat', 'phpat',
                         'trpat', 'ampat', 'mypat', 'idpat', 'kgpat', 'tjpat', 'kzpat', 'uzpat', 'gcpat', 'zapat',
                         'egpat', 'kepat', 'mapat', 'mwpat', 'zmpat', 'tnpat', 'dzpat', 'zwpat', 'oapat', 'appat',
                         'brpat', 'clpat', 'pepat', 'cupat', 'capat', 'mxpat', 'arpat', 'papat', 'ecpat', 'gtpat',
                         'hnpat', 'nipat', 'svpat', 'crpat', 'copat', 'dopat', 'ttpat', 'aupat', 'nzpat', 'emdes']
        self.server = services.ApiServeice(logging=LOGGING)
        self.download = download_middleware.Download_Middleware(logging=LOGGING)
        self.register = register.RegisterBaiTeng()
        self.dao = dao.Dao(logging=LOGGING)
        self.sic_number = 0 # 当前专利分类索引
        self.region_number = 0 # 当前专利地区分类索引
        self.page = 1 # 当前在抓页数
        self.page_count = 0 # 总页数
        self.page_guid = "" # 下一页页码guid
        self.error = ''
        self.proxy = None # 代理IP
        self.innojoy_page_guid = 'innojoy_page_guid_G'  # redis中保存下一页guid的建
        self.innojoy_page_number = 'innojoy_page_number_G'  # redis中保存当前在抓页数的建
        self.innojoy_region_number = 'innojoy_region_number_G'  # redis中保存当前专利地区分类索引的建
        self.innojoy_sic_number = 'innojoy_sic_number_G'  # redis中保存专利分类索引的建

    # 获取专利摘要数据列表
    def getAbstractDataList(self, resp, ua, proxy):
        return_data = []
        try:
            response = json.loads(resp)
        except:
            LOGGING.error('获取当前页专利url - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        # response = resp
        try:
            ErrorInfo = response['ErrorInfo']
            if ErrorInfo == 'no patent found.':

                return None
        except:
            patent_list = response['Option']['PatentList']
            for patent in patent_list:
                data = {}
                # 获取专利标题
                data['title'] = self.server.getPatentTitleField(resp=patent)
                # 获取语种
                data['yuZhong'] = self.server.getPatentYuZhong(resp=patent)
                # 获取下载链接
                data['xiaZaiLianJie'] = self.server.getXiaZaiLianJie(resp=patent)
                # 获取申请号
                data['shenQingHao'] = self.server.getShenQingHao(resp=patent)
                # 获取申请日
                data['shenQingRi'] = self.server.getShenQingRi(resp=patent)
                # 获取公开号
                data['gongKaiHao'] = self.server.getGongKaiHao(resp=patent)
                # 获取公开日
                data['gongKaiRi'] = self.server.getGongKaiRi(resp=patent)
                # 获取当前权利人
                data['dangQianQuanLiRen'] = self.server.getDangQianQuanLiRen(resp=patent)
                # 获取申请人地址
                data['shenQingRenDiZhi'] = self.server.getShenQingRenDiZhi(resp=patent)
                # 获取IPC主分类号
                data['ipcZhuFenLeiHao'] = self.server.getPICZhuFenLeiHao(resp=patent)
                # 获取国省代码
                data['guoShengDaiMa'] = self.server.getGuoShengDaiMa(resp=patent)
                # 获取申请人
                data['shenQingRen'] = self.server.getShenQingRen(resp=patent)
                # 获取发明人
                data['faMingRen'] = self.server.getFaMingRen(resp=patent)
                # 获取IPC分类号
                data['ipcFenLeiHao'] = self.server.getIpcFenLeiHao(resp=patent)
                # 获取CPC分类号
                data['cpcFenLeiHao'] = self.server.getCpcFenLeiHao(resp=patent)
                # 获取ECLA分类号
                data['eclaFenLeiHao'] = self.server.getEclaFenLeiHao(resp=patent)
                # 获取NC分类号
                data['ncFenLeiHao'] = self.server.getNcFenLeiHao(resp=patent)
                # 获取F-Term分类号
                data['fTermFenLeiHao'] = self.server.getFTermFenLeiHao(resp=patent)
                # 获取优先权号
                data['youXianQuanHao'] = self.server.getYouXianQuanHao(resp=patent)
                # 获取国际申请
                data['guoJiShenQing'] = self.server.getGuoJiShenQing(resp=patent)
                # 获取国际公布
                data['guoJiGongBu'] = self.server.getGuoJiGongBu(resp=patent)
                # 获取进入国家日期
                data['jinRuGuoJiaRiQi'] = self.server.getJinRuGuoJiaRiQi(resp=patent)
                # 获取代理机构
                data['daiLiJiGou'] = self.server.getDaiLiJiGou(resp=patent)
                # 获取代理人
                data['daiLiRen'] = self.server.getDaiLiRen(resp=patent)
                # 获取分案原申请号
                data['fenAnYuanShenQingHao'] = self.server.getFenAnYuanShenQingHao(resp=patent)
                # 获取引证专利
                data['yinZhengZhuanLi'] = self.server.getYinZhengZhuanLi(resp=patent)
                # 获取摘要
                data['zhaiYao'] = self.server.getZhaiYao(resp=patent)
                # 获取标识
                try:
                    data['biaoShi'] = self.server.getBiaoShi(resp=patent, ua=ua, proxy=proxy)
                except:
                    data['biaoShi'] = ""
                # 获取主权项
                data['zhuQuanXiang'] = ""
                # 获取说明书
                data['shuoMingShu'] = ""
                # 获取专利国别
                data['zhuanLiGuoBie'] = self.server.getZhuanLiGuoBie(resp=patent)
                # 获取全项数
                data['quanXiangShu'] = self.server.getQuanXiangShu(resp=patent)
                # 获取同族数
                data['tongZuShu'] = self.server.getTongZuShu(resp=patent)
                # 获取授权年度
                data['shouQuanNianDu'] = self.server.getShouQuanNianDu(resp=patent)
                # 获取专利状态
                data['zhuanLiZhuangTai'] = self.server.getZhuanLiZhuangTai(resp=patent)
                # 获取诉讼运营
                data['suSongYunYing'] = self.server.getSuSongYunYing(resp=patent)
                # 获取专利类型
                data['zhuanLiLeiXing'] = self.server.getZhuanLiLeiXing(resp=patent)
                # 生成专利url
                data['url'] = self.server.createPatentUrl(resp=patent)
                # 生成sha
                data['sha'] = self.server.createPatentUrlSha1(patentUrl=data['url'])
                # 生成key
                data['key'] = data['url']
                # 生成ss ——实体
                data['ss'] = '专利'
                # 生成ws ——目标网站
                data['ws'] = 'innojoy专利'
                # 生成clazz ——层级关系
                data['clazz'] = '专利'
                # 生成es ——栏目名称
                data['es'] = '专利'
                # 生成biz ——项目
                data['biz'] = '文献大数据'
                # 生成ref
                data['ref'] = ''

                return_data.append(data)

        return return_data


    def run(self):
        redis_cli = redispool_utils.createRedisPool() # redis连接池
        mysql_cli = mysqlpool_utils.createMysqlPool() # mysql连接池

        while 1:
            # 初始化当前专利分类索引
            self.sic_number = self.dao.getInnojoySicNumber(redis_client=redis_cli, key=self.innojoy_sic_number)
            # 初始化当前专利地区分类索引
            self.region_number = self.dao.getInnojoyRegionNumber(redis_client=redis_cli, key=self.innojoy_region_number)
            # 初始化当前在抓页数
            self.page = self.dao.getInnojoyPage(redis_client=redis_cli, key=self.innojoy_page_number)
            # 初始化下一页页码guid
            self.page_guid = self.dao.getInnojoyPageGuid(redis_client=redis_cli, key=self.innojoy_page_guid)
            self.error = '' # 初始化错误

            ua = user_agent_u.get_ua() # User_Agent
            if self.proxy is None:
                proxy = self.server.getProxy() # 代理IP
                self.proxy = proxy
            else:
                proxy = self.proxy
            if not proxy:
                continue
            redispool_utils.sadd(redis_client=redis_cli, key='innojoy_proxy', value=proxy)
            LOGGING.info('当前ua: {}'.format(ua))
            LOGGING.info('当前代理: {}'.format(proxy))
            # # 获取innojoy账号
            user_data_dict = self.dao.getInnojoyMobile(connection=mysql_cli)
            if user_data_dict:
                user = user_data_dict['mobile']
            else:
                user = self.register.registerBaiTeng(proxies=proxy)
                if user is None:
                    self.proxy = None
                    continue
            if user == '橙子余额不足，请充值':
                LOGGING.error('橙子余额不足， 请充值')
                return
            # user = '13658177914'
            if user is None:
                LOGGING.info('innojoy账号获取失败')
                time.sleep(10)
                continue

            LOGGING.info('当前账号: {}'.format(user))
            # 获取大为账号参数响应
            user_guid_resp = self.download.getUserGuid_resp(user=user, proxy=proxy, ua=ua)
            if user_guid_resp is None:
                LOGGING.error('获取大为账号GUID响应失败')
                self.proxy = None
                continue
            user_guid = self.server.getUserGuid(resp=user_guid_resp) # 大为账号GUID
            if user_guid is None:
                LOGGING.error('提取大为账号GUID失败')

                continue
            if user_guid == '账号不存在！':
                # 从mysql删除当前账号
                LOGGING.error('账号被封： {}'.format(user))
                self.dao.deleteUser(connection=mysql_cli, mobile=user)
                continue

            LOGGING.info('账号GUID: {}'.format(user_guid))
            for sic in self.patent_type_list:
                if self.patent_type_list.index(sic) != self.sic_number:
                    continue
                for region in self.add_list:
                    LOGGING.info(str(self.add_list.index(region)) + str('/') + str(len(self.add_list)))
                    if self.add_list.index(region) != self.region_number:
                        continue

                    # 获取第一页响应
                    one_page_resp = self.download.getPageResp(Query=sic, Database=region, page=1, proxy=proxy, ua=ua,
                                                              guid=user_guid, page_guid='')

                    LOGGING.info('首页响应：' + '\n' + str(one_page_resp) + '\n')
                    if one_page_resp is None:
                        self.error = 1
                        self.proxy = None
                        # 保存当前账号到mysql账号池
                        self.dao.saveInnojoyMobile(mysql_cli=mysql_cli, user=user)
                        break
                    one_page_resp_dict = json.loads(one_page_resp)
                    one_ReturnValue = one_page_resp_dict['ReturnValue']
                    if one_ReturnValue != 0:
                        print(one_page_resp_dict)
                        value = one_page_resp_dict['ErrorInfo']
                        if value == 'verification':
                            self.error = value
                            self.proxy = None
                            break
                        LOGGING.error(value)
                        self.error = value
                        self.proxy = None
                        # 保存当前账号到mysql账号池
                        self.dao.saveInnojoyMobile(mysql_cli=mysql_cli, user=user)
                        break
                    else:
                        self.error = ''

                    # 获取下一页GUID
                    self.page_guid = self.server.getPageGuid(resp=one_page_resp)
                    LOGGING.info('下一页guid: {}'.format(self.page_guid))
                    # 同步下一页guid到redis数据库
                    self.dao.setInnojoyPageGuid(redis_client=redis_cli, key=self.innojoy_page_guid, value=self.page_guid)

                    while 1:
                    # for ii in range(8):
                        LOGGING.info('当前正在抓取第{}个专利分类下的{}地区分类的第{}页'.format(self.sic_number + 1, self.region_number + 1, self.page))
                        # 获取当前页响应
                        page_resp = self.download.getPageResp(Query=sic, Database=region, page=self.page, proxy=proxy, ua=ua,  guid=user_guid, page_guid=self.page_guid)
                        LOGGING.info('当前页响应：' + '\n' + str(page_resp) + '\n')
                        if page_resp is None:
                            self.error = 1
                            self.proxy = None
                            # 保存当前账号到mysql账号池
                            self.dao.saveInnojoyMobile(mysql_cli=mysql_cli, user=user)
                            break
                        # 获取响应状态
                        page_resp_dict = json.loads(page_resp)
                        ReturnValue = page_resp_dict['ReturnValue']
                        if ReturnValue != 0:
                            print(page_resp_dict)
                            value = page_resp_dict['ErrorInfo']
                            # if value == 'verification':
                            #     self.error = value
                            #     self.proxy = None
                            #     break
                            LOGGING.error(value)
                            self.error = value
                            self.proxy = None
                            # 保存当前账号到mysql账号池
                            self.dao.saveInnojoyMobile(mysql_cli=mysql_cli, user=user)
                            break
                        else:
                            self.error = ''

                        # 获取下一页GUID
                        self.page_guid = self.server.getPageGuid(resp=page_resp)
                        # 同步下一页guid到redis数据库
                        self.dao.setInnojoyPageGuid(redis_client=redis_cli, key=self.innojoy_page_guid, value=self.page_guid)
                        # 获取专利总数量
                        count = self.server.getPatentNum(resp=page_resp)
                        # 计算总页数
                        self.page_count = self.server.getPageCount(count=count)
                        # 获取专利摘要数据
                        abstract_data_list = self.getAbstractDataList(resp=page_resp, ua=ua, proxy=proxy)
                        for abstract_data in abstract_data_list:
                            # 存储专利种子到mysql
                            self.dao.saveInnojoyPatentUrl(mysql_client=mysql_cli, url=abstract_data['url'])
                            # TODO 存储专利数据到hbase
                            self.dao.saveInnojoyPatentDataToHbase(data=abstract_data)
                            print(abstract_data['sha'])

                        LOGGING.info('已抓取第{}页'.format(self.page))

                        # 生成下一页
                        self.page += 1
                        # 同步当前页数到redis
                        self.dao.setInnojoyPage(redis_client=redis_cli, key=self.innojoy_page_number, value=self.page)
                        # 判断当前是否是最后一页
                        if self.page > self.page_count:
                            self.page = 1 # 初始化页数
                            # 同步当前页数到redis
                            self.dao.setInnojoyPage(redis_client=redis_cli, key=self.innojoy_page_number, value=self.page)
                            break

                        time.sleep(5)
                        # break
                    LOGGING.info('结束翻页')
                    if self.error != '':
                        break
                    else:
                        # 判断当前是否是最后一页
                        if self.page > self.page_count:
                            self.region_number += 1
                            # 同步当前专利地区分类索引到redis
                            self.dao.setInnojoyRegionNumber(redis_client=redis_cli, key=self.innojoy_region_number, value=self.region_number)
                        else:
                            break

                    # break

                if self.error != '':
                    break
                else:
                    # 判断当前分类是否已达到最后一个分类
                    if self.region_number == len(self.add_list):
                        self.sic_number += 1
                        # 同步当前专利分类索引到redis
                        self.dao.setInnojoySicNumber(redis_client=redis_cli, key=self.innojoy_sic_number, value=self.sic_number)
                    else:
                        break

            if self.sic_number == len(self.patent_type_list):
                # 初始化所有参数
                self.sic_number = 0  # 当前专利分类索引
                # 同步当前专利分类索引到redis
                self.dao.setInnojoySicNumber(redis_client=redis_cli, key=self.innojoy_sic_number, value=self.sic_number)
                self.region_number = 0  # 当前专利地区分类索引
                # 同步当前专利地区分类索引到redis
                self.dao.setInnojoyRegionNumber(redis_client=redis_cli, key=self.innojoy_region_number, value=self.region_number)
                self.page = 1  # 当前在抓页数
                # 同步当前页数到redis
                self.dao.setInnojoyPage(redis_client=redis_cli, key=self.innojoy_page_number, value=self.page)
                self.page_count = 0  # 总页数
                self.page_guid = ""  # 下一页页码guid
                self.error = ''


            #         break
            #     break
            #
            # break


if __name__ == '__main__':
    main = SpiderMain()
    main.run()
    # main.getAbstractDataList(resp=demo_data)
