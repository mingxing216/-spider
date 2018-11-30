# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import re
import random
import json
import base64
import hashlib
from lxml import html
from PIL import Image
from selenium import webdriver

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
import settings
from Log import log
from Project.DaWeiSpiderProject.middleware import download_middleware
from Project.DaWeiSpiderProject.dao import dao
from Downloader import downloader
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
        self.dao = dao.Dao(logging=logging)

    # 从芝麻代理API获取一个短效代理IP
    def getProxy(self):
        try:
            proxy = proxy_utils.getZhiMaProxy_SetMeal(set_meal=self.ZHIMA_SETMEAL, num=1)[0]
        except Exception as e:
            self.logging.error('未获取到代理IP')
            self.getProxy()
        else:
            if proxy:
                proxy_ip = "{}:{}".format(proxy['ip'], proxy['port'])
                proxy = {
                    'http': 'socks5://{}'.format(proxy_ip),
                    'https': 'socks5://{}'.format(proxy_ip)
                }

                return proxy

    # 从芝麻代理API获取一个短效IP——按次提取
    def getProxy_one(self):
        try:
            proxy = proxy_utils.getZhiMaProxy_Number(num=1)[0]
        except Exception as e:
            self.logging.error('未获取到代理IP')
            self.getProxy()
        else:
            if proxy:
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

    # 获取专利总数量
    def getPatentNum(self, resp):
        return_data = []
        try:
            response = json.loads(resp)
        except:
            self.logging.error('获取当前页专利url - 响应转换dict失败。 响应内容: {}, 响应类型: {}'.format(resp, type(resp)))
            return None
        count = response['Option']['Count']
        # patent_list = response['Option']['PatentList']
        # for patent in patent_list:
        #     Dn = patent['DN']
        #     url = 'http://www.innojoy.com/patent/patent.html?docno={}&trsdb={}&showList=true'.format(Dn, Database)
        #     return_data.append(url)

        # database: 地区分类号， count: 当前分类包含的专利总数量， return_data: 专利url列表
        return count

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

    # 将innojoy账号存回redis数据库【仅种子爬虫用】
    def saveInnojoyMobileToUrlSpider(self, redis_client, value):
        redispool_utils.sadd(redis_client=redis_client, key=self.innojoy_mobilepool_url_spider, value=value)

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
        title = resp['TI']
        try:
            title = re.findall(r"(.*?)\[.*\]", title)[0]
            return title
        except:
            return ""

    # 提取专利语种
    def getPatentYuZhong(self, resp):
        title = resp['TI']
        try:
            yuZhong_data = re.findall(r".*?(\[.*\])", title)[0]
            yuZhong = re.sub(r'(\[|\])', '', yuZhong_data)
            return yuZhong
        except:
            return ""

    # 提取专利下载链接
    def getXiaZaiLianJie(self, resp):
        # http://www.innojoy.com/client/file/["fmzl","CN201810359894.1","BOOKS@FM@2018@20181109@201810359894.1"]/CN201810359894.1-一种农业用黑麦草收割设备[ZH].PDF?
        try:
            # 获取地区分类号
            region_number = resp['DB']
            # 获取专利号
            patent_number = resp['DN']
            # 获取下载必要参数
            down_data = resp['PP']
            down_data = re.sub(r"/", '@', down_data)
            # 获取标题
            title = resp['TI']
            # 生成下载链接
            url = ('http://www.innojoy.com/client/file/'
                   '["%s","%s","%s"]/%s-%s.PDF?' % (region_number, patent_number, down_data, patent_number, title))
        except:
            url = ""

        return url

    # 获取申请号
    def getShenQingHao(self, resp):
        shenQingHao = resp['DN']

        return shenQingHao

    # 获取申请日
    def getShenQingRi(self, resp):
        shenQingRi_data = resp['AD']
        shenQingRi = re.sub(r'(\.)', '-', shenQingRi_data) + ' ' + '00:00:00'

        return shenQingRi

    # 获取公开号
    def getGongKaiHao(self, resp):
        gongKaiHao = resp['PNM']

        return gongKaiHao

    # 获取公开日
    def getGongKaiRi(self, resp):
        gongKaiRi_data = resp['PD']
        gongKaiRi = re.sub(r'(\.)', '-', gongKaiRi_data) + ' ' + '00:00:00'

        return gongKaiRi

    # 获取当前权利人
    def getDangQianQuanLiRen(self, resp):
        dangQianQuanLiRen = resp['CAS']

        return dangQianQuanLiRen

    # 获取申请人地址
    def getShenQingRenDiZhi(self, resp):
        shenQingRenDiZhi = resp['AR']

        return shenQingRenDiZhi

    # 获取IPC主分类号
    def getPICZhuFenLeiHao(self, resp):
        PICZhuFenLeiHao = resp['PIC']

        return PICZhuFenLeiHao

    # 获取国省代码
    def getGuoShengDaiMa(self, resp):
        guoShengDaiMa = resp['CO']

        return guoShengDaiMa

    # 获取申请人
    def getShenQingRen(self, resp):
        shenQingRen_data = resp['PPA']
        shenQingRen = re.sub(r'(;|；)', '|', shenQingRen_data)

        return shenQingRen

    # 获取发明人
    def getFaMingRen(self, resp):
        faMingRen_data = resp['INNTMS']
        faMingRen = re.sub(r'(;|；)', '|', faMingRen_data)

        return faMingRen

    # 获取IPC分类号
    def getIpcFenLeiHao(self, resp):
        ipcFenLeiHao_data = resp['SIC']
        ipcFenLeiHao = re.sub(r'(;|；)', '|', ipcFenLeiHao_data)

        return ipcFenLeiHao

    # 获取CPC分类号
    def getCpcFenLeiHao(self, resp):
        cpcFenLeiHao_data = resp['CPC']
        cpcFenLeiHao = re.sub(r'(;|；)', '|', cpcFenLeiHao_data)

        return cpcFenLeiHao

    # 获取ECLA分类号
    def getEclaFenLeiHao(self, resp):
        eclaFenLeiHao_data = resp['SEC']
        eclaFenLeiHao = re.sub(r'(;|；)', '|', eclaFenLeiHao_data)

        return eclaFenLeiHao

    # 获取NC分类号
    def getNcFenLeiHao(self, resp):
        ncFenLeiHao_data = resp['SNC']
        ncFenLeiHao = re.sub(r'(;|；)', '|', ncFenLeiHao_data)

        return ncFenLeiHao

    # 获取F-Term分类号
    def getFTermFenLeiHao(self, resp):
        fTermFenLeiHao_data = resp['FTERM']
        fTermFenLeiHao = re.sub(r'(;|；)', '|', fTermFenLeiHao_data)

        return fTermFenLeiHao

    # 获取优先权号
    def getYouXianQuanHao(self, resp):
        youXianQuanHao_data = resp['PR']
        youXianQuanHao = re.sub(r'(;|；)', '|', youXianQuanHao_data)

        return youXianQuanHao

    # 获取国际申请
    def getGuoJiShenQing(self, resp):
        guoJiShenQing_data = resp['IAN']
        guoJiShenQing = re.sub(r'(;|；)', '|', guoJiShenQing_data)

        return guoJiShenQing

    # 获取国际公布
    def getGuoJiGongBu(self, resp):
        guoJiGongBu_data = resp['IPN']
        guoJiGongBu = re.sub(r'(;|；)', '|', guoJiGongBu_data)

        return guoJiGongBu

    # 获取进入国家日期
    def getJinRuGuoJiaRiQi(self, resp):
        jinRuGuoJiaRiQi_data = resp['DEN']
        jinRuGuoJiaRiQi = re.sub(r'(\.)', '-', jinRuGuoJiaRiQi_data) + ' ' + '00:00:00'

        return jinRuGuoJiaRiQi

    # 获取代理机构
    def getDaiLiJiGou(self, resp):
        daiLiJiGou = resp['AGC']

        return daiLiJiGou

    # 获取代理人
    def getDaiLiRen(self, resp):
        daiLiRen_data = resp['AGT']
        daiLiRen = re.sub(r'(;|；)', '|', daiLiRen_data)

        return daiLiRen

    # 获取分案原申请号
    def getFenAnYuanShenQingHao(self, resp):
        fenAnYuanShenQingHao = resp['DAN']

        return fenAnYuanShenQingHao

    # 获取引证专利
    def getYinZhengZhuanLi(self, resp):
        yinZhengZhuanLi_data = resp['REFP']
        yinZhengZhuanLi = re.sub(r'(;|；)', '|', yinZhengZhuanLi_data)

        return yinZhengZhuanLi

    # 获取摘要
    def getZhaiYao(self, resp):
        return_data = ""
        zhaiYao_data = resp['CD']
        zhaiYao_data_etree = etree.HTML(zhaiYao_data)
        zhaiyao_html = zhaiYao_data_etree.xpath("//abstract[@lang]")
        for html in zhaiyao_html:
            zhaiYao = etree.tostring(html)
            return_data = return_data + zhaiYao.decode('utf-8') + '\n'

        return return_data

    # 获取标识
    def getBiaoShi(self, resp,  ua, proxy):
        referer = 'http://www.innojoy.com'
        down_url = resp['MP']
        download = download_middleware.Download_Middleware(logging=self.logging)
        img_data = download.downImg(url=down_url, referer=referer, ua=ua)
        # with open('{}.png'.format(hashlib.sha1(down_url.encode('utf-8')).hexdigest()), 'wb') as f:
        #     f.write(img_data)
        img_data_bs64 = base64.b64encode(img_data)
        # 保存图片
        sha = hashlib.sha1(down_url.encode('utf-8')).hexdigest()
        self.logging.info('图片sha: {}'.format(sha))
        item = {
            'pk': sha,
            'type': 'image',
            'url': down_url
        }
        save_status = self.dao.saveInnojoyPatentImageToHbase(media_url=down_url, content=img_data_bs64, type='image', item=item)
        status_dict = json.loads(save_status)
        resultcode = status_dict['resultCode']

        if resultcode == 0:
            return down_url

        else:
            return ""

    # 获取主权项
    def getZhuQuanXiang(self, resp):
        zhuQuanXiang = resp['FD']

        return zhuQuanXiang

    # 获取说明书
    def getShuoMingShu(self, resp):


        return ""

    # 获取专利国别
    def getZhuanLiGuoBie(self, resp):
        zhuanLiGuoBie = resp['DBName']

        return zhuanLiGuoBie

    # 获取全项数
    def getQuanXiangShu(self, resp):
        quanXiangShu = resp['CLMN']

        return quanXiangShu

    # 获取同族数
    def getTongZuShu(self, resp):
        tongZuShu = resp['FMLN']

        return tongZuShu

    # 获取授权年度
    def getShouQuanNianDu(self, resp):

        return ""

    # 获取专利状态
    def getZhuanLiZhuangTai(self, resp):
        zhuanLiZhuangTai = resp['CLS']

        return zhuanLiZhuangTai

    # 获取诉讼运营
    def getSuSongYunYing(self, resp):
        suSongYunYing_data = resp['GZSX']
        suSongYunYing = re.sub(r'(;|；)', '|', suSongYunYing_data)

        return suSongYunYing

    # 获取专利类型
    def getZhuanLiLeiXing(self, resp):
        zhuanLiLeiXing = resp['PAT']

        return zhuanLiLeiXing

    # 生成专利url
    def createPatentUrl(self, resp):
        # 获取申请号
        shenQingHao = resp['DN']
        diQuHao = resp['DB']
        url = 'http://www.innojoy.com/patent/patent.html?docno={}&trsdb={}&showList=true'.format(shenQingHao,
                                                                                                 diQuHao)

        return url

    # 生成sha
    def createPatentUrlSha1(self, patentUrl):
        sha = hashlib.sha1(patentUrl.encode('utf-8')).hexdigest()

        return sha


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
    def getProxy(self):
        while 1:
            proxy = proxy_utils.getZhiMaProxy_SetMeal(set_meal=settings.ZHIMA_SETMEAL, num=1, protocol=1)[0]
            proxy = "{}:{}".format(proxy['ip'], proxy['port'])

            proxies = "http://{}".format(proxy)
            # 检测代理是否高匿
            status = proxy_utils.jianChaNiMingDu(proxy=proxies, logging=self.logging)
            if status:

                return proxy
            else:
                self.logging.error('代理不是高匿')
                continue

    # 创建selenium driver
    def creatDriver(self, proxy, ua):
        # Chrom
        # chromeOptions = webdriver.ChromeOptions()
        # chromeOptions.add_argument("--proxy-server=http://%s" % proxy)
        # chromeOptions.add_argument("--user-agent=%s" % ua)
        # driver = webdriver.Chrome(chrome_options=chromeOptions)
        # driver.set_window_size(1920, 1080)
        # # driver.maximize_window()
        # driver.implicitly_wait(10)
        # driver.set_page_load_timeout(10)
        #
        # return driver

        chromeOptions = webdriver.ChromeOptions()

        chromeOptions.set_headless()
        chromeOptions.add_argument("--proxy-server=http://%s" % proxy)
        chromeOptions.add_argument("--user-agent=%s" % ua)
        chromeOptions.add_argument("lang=zh_CN.UTF-8")
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(10)

        return driver

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



# log_file_dir = 'DaWeiSpiderProject'  # LOG日志存放路径
# LOGNAME = '<大为专利账号注册>'  # LOG名
# LOGGING = log.ILog(log_file_dir, LOGNAME)
# if __name__ == '__main__':
#     demo = Services(LOGGING)
#     status = demo.getProxy()
#     print(status)


