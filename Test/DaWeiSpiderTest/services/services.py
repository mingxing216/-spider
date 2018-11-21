# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import time
import re
import random
import json
from lxml import html
from PIL import Image
from selenium import webdriver

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Test.DaWeiSpiderTest.middleware import download_middleware
from Utils import proxy_utils
from Utils import dir_utils
from Utils import RuoKuaiVerify
from Utils import redispool_utils

etree = html.etree

class ApiServeice(object):
    def __init__(self, logging):
        self.logging = logging
        self.innojoy_mobilepool_url_spider = 'innojoy_mobilepool_url_spider' # redis中种子爬虫专用账号池
        self.innojoy_mobile = 'innojoy_mobile'  # redis中保存innojoy账号的集合名
        self.ZHIMA_SETMEAL = settings.ZHIMA_SETMEAL

    # 从芝麻代理API获取一个短效代理IP
    def getProxy(self):
        proxy = proxy_utils.getZhiMaProxy_SetMeal(set_meal=self.ZHIMA_SETMEAL, num=1)[0]
        proxy_ip = "{}:{}".format(proxy['ip'], proxy['port'])
        proxy = {
            'http': 'socks5://{}'.format(proxy_ip),
            'https': 'socks5://{}'.format(proxy_ip)
        }

        return proxy

    # 提取大为账号GUID
    def getUserGuid(self, resp):
        try:
            response = json.loads(resp)
        except:
            self.logging.error('提取大为账号GUID - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        try:
            GUID = response['Option']['GUID']
        except:
            self.logging.error('提取大为账号GUID - 提取失败。 响应内容: {}, 响应类型: {}'.format(response, type(response)))
            return None
        else:

            return GUID

    # 提取专利分类ID列表
    def getSicList(self, resp):
        return_data = []
        try:
            response = json.loads(resp)
        except:
            self.logging.error('提取专利分类ID列表 - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        TreeInfo = response['Option']['TreeInfo']
        if not TreeInfo:
            self.logging.error('提取专利分类ID列表 - 获取分类列表失败。 响应内容: {}, 响应类型: {}'.format(TreeInfo, type(TreeInfo)))
            return None
        for info in TreeInfo:
            sic = info['dataObject']['SIC']
            return_data.append(sic)

        return return_data

    # 提取专利地区分类参数
    def getRgionList(self, resp):
        try:
            datas = re.findall(r"DBS=({.*?})", resp)[0]
        except:
            self.logging.error('提取专利地区分类参数 - 获取分类列表失败。')
            datas = None
        if datas:
            datas = re.sub(',+', ',', re.sub('([A-Z]+:|\")', '', re.sub('}', ')', re.sub('{', '(', datas))))
            datas = eval(re.sub(',', '","', re.sub(r'\)', '")', re.sub(r'\(', '("', datas))))

            return datas

        return None

    # 获取下一页GUID
    def getPageGuid(self, resp):
        try:
            response = json.loads(resp)
        except:
            self.logging.error('获取下一页GUID - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        try:
            GUID = response['Option']['GUID']
        except:
            self.logging.error('获取下一页GUID - 提取下一页GUID失败。 响应内容: {}, 响应类型: {}'.format(response, type(response)))
            return None
        else:

            return GUID

    # 获取当前页专利url
    def getPatentUrlList(self, resp):
        return_data = []
        try:
            response = json.loads(resp)
        except:
            self.logging.error('获取当前页专利url - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        try:
            Database = response['Option2']
        except:
            return None
        count = response['Option']['Count']
        patent_list = response['Option']['PatentList']
        for patent in patent_list:
            Dn = patent['DN']
            url = 'http://www.innojoy.com/patent/patent.html?docno={}&trsdb={}&showList=true'.format(Dn, Database)
            return_data.append(url)

        # database: 地区分类号， count: 当前分类包含的专利总数量， return_data: 专利url列表
        return count, return_data

    # 计算总页数
    def getPageCount(self, count):
        if count % 50 != 0:
            page_count = (count / 50) + 1

            return page_count
        else:
            page_count = int(count / 50)

            return page_count

    # 从redis获取并删除innojoy账号【仅种子爬虫用】
    def getInnojoyMobileToUrlSpider(self, redis_client):
        mobile = redispool_utils.queue_spop(redis_client=redis_client, key=self.innojoy_mobilepool_url_spider, lockname='innojoy_mobilepool_url_spider_lock')

        return mobile

    # 从redis获取innojoy账号
    def getInnojoyMobiles(self, redis_client):
        try:
            mobile = redispool_utils.srandmember(redis_client=redis_client, key=self.innojoy_mobile, num=1)[0]
        except:
            mobile = None

        return mobile

    # 从redis删除innojoy账号
    def delInnojoyMobile(self, redis_client, key, value):
        redispool_utils.srem(redis_client=redis_client, key=key, value=value)

    # 从任务中获取专利号
    def getPatentNumber(self, resp):
        try:
            patent_number = re.findall(r"docno=(.*?)&", resp)[0]
            return patent_number
        except:
            return None

    # 从任务中获取地区分类号
    def getPatentRegionNumber(self, resp):
        try:
            patent_region_number = re.findall(r"trsdb=(.*?)&", resp)[0]
            return patent_region_number
        except:
            return None

    # ==============字段提取================
    # 提取专利标题
    def getPatentTitleField(self, resp):
        title = resp['Option']['PatentList'][0]['TI']
        try:
            title = re.findall(r"(.*?)\[.*\]", title)[0]
            return title
        except:
            return ""

    # 提取专利语种
    def getPatentYuZhong(self, resp):
        title = resp['Option']['PatentList'][0]['TI']
        try:
            yuZhong = re.findall(r".*?(\[.*\])", title)[0]
            return yuZhong
        except:
            return ""

    # 提取专利下载链接
    def getXiaZaiLianJie(self, resp):
        # http://www.innojoy.com/client/file/["fmzl","CN201810359894.1","BOOKS@FM@2018@20181109@201810359894.1"]/CN201810359894.1-一种农业用黑麦草收割设备[ZH].PDF?
        try:
            # 获取地区分类号
            region_number = resp['Option']['PatentDataBase']
            # 获取专利号
            patent_number = resp['Option']['PatentList'][0]['DN']
            # 获取下载必要参数
            down_data = resp['Option']['PatentList'][0]['PP']
            down_data = re.sub(r"/", '@', down_data)
            # 获取标题
            title = resp['Option']['PatentList'][0]['TI']
            # 生成下载链接
            url = ('http://www.innojoy.com/client/file/'
                   '["%s","%s","%s"]/%s-%s.PDF?' % (region_number, patent_number, down_data, patent_number, title))
        except:
            url = ""

        return url

    # 获取申请号
    def getShenQingHao(self, resp):
        shenQingHao = resp['Option']['PatentList'][0]['DN']

        return shenQingHao

    # 获取申请日
    def getShenQingRi(self, resp):
        shenQingRi = resp['Option']['PatentList'][0]['AD']

        return shenQingRi

    # 获取公开号
    def getGongKaiHao(self, resp):
        gongKaiHao = resp['Option']['PatentList'][0]['PNM']

        return gongKaiHao

    # 获取公开日
    def getGongKaiRi(self, resp):
        gongKaiRi = resp['Option']['PatentList'][0]['PD']

        return gongKaiRi

    # 获取当前权利人
    def getDangQianQuanLiRen(self, resp):
        dangQianQuanLiRen = resp['Option']['PatentList'][0]['CAS']

        return dangQianQuanLiRen

    # 获取申请人地址
    def getShenQingRenDiZhi(self, resp):
        shenQingRenDiZhi = resp['Option']['PatentList'][0]['AR']

        return shenQingRenDiZhi

    # 获取IPC主分类号
    def getPICZhuFenLeiHao(self, resp):
        PICZhuFenLeiHao = resp['Option']['PatentList'][0]['PIC']

        return PICZhuFenLeiHao

    # 获取国省代码
    def getGuoShengDaiMa(self, resp):
        guoShengDaiMa = resp['Option']['PatentList'][0]['CO']

        return guoShengDaiMa

    # 获取申请人
    def getShenQingRen(self, resp):
        shenQingRen = resp['Option']['PatentList'][0]['PPA']

        return shenQingRen

    # 获取发明人
    def getFaMingRen(self, resp):
        faMingRen = resp['Option']['PatentList'][0]['INNTMS']

        return faMingRen

    # 获取IPC分类号
    def getIpcFenLeiHao(self, resp):
        ipcFenLeiHao = resp['Option']['PatentList'][0]['SIC']

        return ipcFenLeiHao

    # 获取CPC分类号
    def getCpcFenLeiHao(self, resp):
        cpcFenLeiHao = resp['Option']['PatentList'][0]['CPC']

        return cpcFenLeiHao

    # 获取ECLA分类号
    def getEclaFenLeiHao(self, resp):
        eclaFenLeiHao = resp['Option']['PatentList'][0]['SEC']

        return eclaFenLeiHao

    # 获取NC分类号
    def getNcFenLeiHao(self, resp):
        ncFenLeiHao = resp['Option']['PatentList'][0]['SNC']

        return ncFenLeiHao

    # 获取F-Term分类号
    def getFTermFenLeiHao(self, resp):
        fTermFenLeiHao = resp['Option']['PatentList'][0]['FTERM']

        return fTermFenLeiHao

    # 获取优先权号
    def getYouXianQuanHao(self, resp):
        youXianQuanHao = resp['Option']['PatentList'][0]['PR']

        return youXianQuanHao

    # 获取国际申请
    def getGuoJiShenQing(self, resp):
        guoJiShenQing = resp['Option']['PatentList'][0]['IAN']

        return guoJiShenQing

    # 获取国际公布
    def getGuoJiGongBu(self, resp):
        guoJiGongBu = resp['Option']['PatentList'][0]['IPN']

        return guoJiGongBu

    # 获取进入国家日期
    def getJinRuGuoJiaRiQi(self, resp):
        jinRuGuoJiaRiQi = resp['Option']['PatentList'][0]['DEN']

        return jinRuGuoJiaRiQi

    # 获取代理机构
    def getDaiLiJiGou(self, resp):
        daiLiJiGou = resp['Option']['PatentList'][0]['AGC']

        return daiLiJiGou

    # 获取代理人
    def getDaiLiRen(self, resp):
        daiLiRen = resp['Option']['PatentList'][0]['AGT']

        return daiLiRen

    # 获取分案原申请号
    def getFenAnYuanShenQingHao(self, resp):
        fenAnYuanShenQingHao = resp['Option']['PatentList'][0]['DAN']

        return fenAnYuanShenQingHao

    # 获取引证专利
    def getYinZhengZhuanLi(self, resp):
        yinZhengZhuanLi = resp['Option']['PatentList'][0]['REFP']

        return yinZhengZhuanLi

    # 获取摘要
    def getZhaiYao(self, resp):
        zhaiYao = resp['Option']['PatentList'][0]['CD']

        return zhaiYao

    # TODO 获取标识， 需要采集图片
    def getBiaoShi(self, resp, referer, ua):
        down_url = resp['Option']['PatentList'][0]['MP']
        download = download_middleware.Download_Middleware(logging=self.logging)
        img_data = download.downImg(url=down_url, referer=referer, ua=ua)

        return img_data

    # 获取主权项
    def getZhuQuanXiang(self, resp):
        zhuQuanXiang = resp['Option']['PatentList'][0]['FD']

        return zhuQuanXiang

    # 获取说明书
    def getShuoMingShu(self, resp):


        return ""

    # 获取专利国别
    def getZhuanLiGuoBie(self, resp):
        zhuanLiGuoBie = resp['Option']['ResultSection'][0]['DbName']

        return zhuanLiGuoBie

    # 获取全项数
    def getQuanXiangShu(self, resp):
        quanXiangShu = resp['Option']['PatentList'][0]['CLMN']

        return quanXiangShu

    # 获取同族数
    def getTongZuShu(self, resp):
        tongZuShu = resp['Option']['PatentList'][0]['FMLN']

        return tongZuShu

    # 获取授权年度
    def getShouQuanNianDu(self, resp):

        return ""

    # 获取专利状态
    def getZhuanLiZhuangTai(self, resp):
        zhuanLiZhuangTai = resp['Option']['PatentList'][0]['CLS']

        return zhuanLiZhuangTai

    # 获取诉讼运营
    def getSuSongYunYing(self, resp):

        return ""


class Services(object):
    def __init__(self, logging):
        self.logging = logging

    # 登录橙子API
    def landingAPI(self, uid, pwd):
        '''登录橙子API'''
        landing_url = 'http://www.517orange.com:9000/devApi/loginIn?uid={}&pwd={}'.format(uid, pwd)
        download = download_middleware.Download_Middleware(logging=self.logging)
        landing_data = download.getOrangeApiData(url=landing_url)
        landing_data = json.loads(landing_data)

        return landing_data

    # 获取一个橙子手机号
    def getPhoneNumber(self, uid, pid, token):
        url = 'http://www.517orange.com:9000/devApi/getMobilenum?uid={}&pid={}&token={}'.format(uid, pid, token)
        download = download_middleware.Download_Middleware(logging=self.logging)
        while True:
            landing_data = download.getOrangeApiData(url=url)
            if landing_data != 'no_data':
                time.sleep(5)
                return landing_data
            else:
                time.sleep(5)
                continue

    # 获取手机短信验证码
    def getMobileVerifyCode(self, uid, pid, mobile, token):
        download = download_middleware.Download_Middleware(logging=self.logging)
        url = ('http://www.517orange.com:9000/devApi/getVcodeAndReleaseMobile?'
               'uid={}'
               '&pid={}'
               '&mobile={}'
               '&token={}'.format(uid, pid, mobile, token))
        for i in range(20):
            data = download.getOrangeApiData(url=url)
            if data != 'no_data':
                mobile_verify_code = re.findall(r"验证码(\d+)，", data)[0]

                return mobile_verify_code
            else:
                time.sleep(5)
                self.logging.info('还未获取到验证码，尝试第{}次'.format(i + 1))
                continue

        return None

    # 释放一个手机号
    def cancelSMSRecv(self, uid, pid, mobile, token):
        url = 'http://www.517orange.com:9000/devApi/cancelSMSRecv?uid={}&pid={}&mobile={}&token={}'.format(uid,
                                                                                                           pid,
                                                                                                           mobile,
                                                                                                           token)
        download = download_middleware.Download_Middleware(logging=self.logging)
        landing_data = download.getOrangeApiData(url=url)

        return landing_data

    # 从芝麻代理接口获取一个短效代理IP【http协议】
    def getProxy(self, redis_client, logging):
        proxy = proxy_utils.getZhiMaProxy_Number(num=1, protocol=1)[0]
        proxy = "{}:{}".format(proxy['ip'], proxy['port'])

        return proxy

    # 创建selenium driver
    def creatDriver(self, proxy, ua):
        # Chrom
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--proxy-server=http://%s" % proxy)
        chromeOptions.add_argument("--user-agent=%s" % ua)
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(10)

        return driver

        # chromeOptions = webdriver.ChromeOptions()
        #
        # chromeOptions.set_headless()
        # chromeOptions.add_argument("--proxy-server=http://%s" % proxy)
        # chromeOptions.add_argument("--user-agent=%s" % ua)
        # chromeOptions.add_argument("lang=zh_CN.UTF-8")
        # driver = webdriver.Chrome(chrome_options=chromeOptions)
        # driver.set_window_size(1920, 1080)
        # driver.implicitly_wait(10)
        # driver.set_page_load_timeout(10)
        #
        # return driver

    # 判断selenium页面是否加载完成
    def judgeHtmlComplete(self, driver, xpath):
        wait = 60
        begin_time = time.time()
        while True:
            try:
                element = driver.find_element_by_xpath("{}".format(xpath))
            except:
                wait_time = time.time() - begin_time
                if wait_time <= wait:
                    self.logging.info('正在加载页面')
                    continue
                else:

                    return False
            else:
                self.logging.info('页面加载完成')

                return True

    # 获取并输入图片验证码
    def get_or_input_img_verify(self, driver):
        # 获取图片验证码
        img = self.getVerifyImg(driver=driver)
        # 破解图片验证码
        verify_code = self.getVerifyCode(img=img, r_Typeid=3000)
        # 输入图片验证码
        driver.find_element_by_id('idChkResultTxt').click()
        driver.find_element_by_id('idChkResultTxt').send_keys(verify_code)

        return img

    # 获取注册验证码图片
    def getVerifyImg(self, driver):
        # 验证码路径
        img = os.path.dirname(__file__) + os.sep + "../../../" + "Static/Img/{}".format('register_verify_{}.png'.
                                                                                        format(random.randint(1, 10000)))
        # 截图
        driver.save_screenshot(img)
        element = driver.find_element_by_id('idChkImage')
        left = int(element.location['x'])
        top = int(element.location['y'])
        right = int(element.location['x'] + element.size['width'])
        bottom = int(element.location['y'] + element.size['height'])
        im = Image.open(img)
        im = im.crop((left, top, right, bottom))
        # 删除截图
        dir_utils.deleteFile(img)
        # 保存验证码截图
        im.save(img)

        return img

    # 破解图片验证码
    def getVerifyCode(self, img, r_Typeid):
        server = RuoKuaiVerify.RClient(username=settings.r_username, password=settings.r_password,
                                       soft_id=settings.r_soft_id, soft_key=settings.r_soft_key)
        im = open(img, 'rb').read()
        try:
            r = server.rk_create(im, r_Typeid)
            code = r['Result']
        except:
            self.logging.error('验证码破解失败')
            code = None

        return code

    # 登录Innojoy
    def langingInnojoy(self,url, user, pwd, driver):
        user = user
        password = pwd

        driver.get(url)
        time.sleep(10)
        driver.switch_to_frame('_userlogin')
        driver.find_element_by_id('idPhone').click()
        driver.find_element_by_id('idPhone').send_keys(user)
        driver.find_element_by_id('idPassword').click()
        driver.find_element_by_id('idPassword').send_keys(password)
        driver.find_element_by_id('quote_sign').click()
        time.sleep(10)

    # 获取分类数量
    def getClassifiedQuantity(self, driver):
        tr_list = driver.find_elements_by_xpath("//a[@class='lasttd']")
        number = len(tr_list)

        return tr_list, number


