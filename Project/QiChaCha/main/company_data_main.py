# -*-coding:utf-8-*-
import sys
import os
import re
import hashlib
import time

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

from Log import log
from Utils import redispool_utils
from Utils import create_ua_utils
from Utils import proxy_utils
from Project.QiChaCha.dao import dao
from Project.QiChaCha.middleware import download_middleware
from Project.QiChaCha.services import services

log_file_dir = 'QiChaCha'  # LOG日志存放路径
LOGNAME = '<企查查数据抓取>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)

class SpiderMain(object):
    def __init__(self, cookie, user_agent):
        self.dao = dao.Dao()
        self.download = download_middleware.Download(cookies=cookie, user_agent=user_agent)
        self.server = services.Services_GetData()
        self.proxies = {}
        self.proxies_status = 1

    def handle(self, obj, proxies):
        save_data = {}
        # 获取电脑端任务响应
        resp_pc = self.download.getJiGouHtml(logging=LOGGING, url=obj, proxies=proxies)
        if resp_pc is None:
            LOGGING.error('电脑端页面获取失败')

            return {'status': 3, 'err': '电脑端页面获取失败'}

        # 获取手机端任务响应
        url = re.sub(r"cbase_", "firm_", re.sub(r"//www\.", "//m.", obj))
        resp_mobile = self.download.getJiGouHtml(logging=LOGGING, url=url, proxies=proxies)
        if resp_mobile is None:
            LOGGING.error('手机端页面获取失败')

            return {'status': 4, 'err': '手机端页面获取失败'}

        # 判断电脑端和手机端页面是否全部完整获取响应
        status = self.server.getHtmlStatus(loggong=LOGGING, resp_pc=resp_pc, resp_mobile=resp_mobile)
        if status['status'] == 1:
            LOGGING.error('遇到验证码')

            return status

        elif status['status'] == 2:
            LOGGING.error('电脑或手机版页面显示不完整')

            return status

        LOGGING.info('全部页面获取成功')

        # 标题
        save_data['title'] = self.server.getTitle(resp=resp_mobile)
        # 标识
        save_data['biaoShi'] = self.server.getBiaoShi(logging=LOGGING, resp=resp_pc)
        # 邮箱
        save_data['email'] = self.server.getEmail(resp=resp_mobile)
        # 简介
        save_data['jianJie'] = self.server.getJianJie(resp=resp_pc)
        # 主页
        save_data['zhuYe'] = self.server.getZhuYe(resp=resp_pc)
        # 所在地_内容
        save_data['suoZaiDi_NeiRong'] = self.server.getSuoZaiDi_Nei(resp=resp_mobile)
        # 点击量
        save_data['dianJiLiang'] = self.server.getDianJiLiang(resp=resp_pc)
        # 生成发票抬头接口
        keyno = re.findall(r"cbase_(.*)", obj)[0]
        new_url = 'https://www.qichacha.com/tax_view?keyno={}&ajaxflag=1'.format(keyno)
        # 下载发票抬头响应
        invoice = self.download.getJiGouHtml(logging=LOGGING, url=new_url, proxies=proxies)
        # 电话
        save_data['dianHua'] = self.server.getDianHua(resp=invoice)
        # 开户银行
        save_data['kaiHuYinHang'] = self.server.getKaiHuYinHang(resp=invoice)
        # 银行账号
        save_data['yinHangZhangHao'] = self.server.getYinHangZhangHao(resp=invoice)
        # 法定代表人信息
        save_data['faDingDaiBiaoRenXinXi'] = self.server.getFaDingDaiBiaoRen(resp=resp_mobile)
        # 注册资本
        save_data['zhuCeZiBen'] = self.server.getZhuCeZiBen(resp=resp_mobile)
        # 经营状态
        save_data['jingYingZhuangTai'] = self.server.getJingYingZhuangTai(resp=resp_mobile)
        # 统一社会信用代码
        save_data['tongYiSheHuiXinYongDaiMa'] = self.server.getTongYiSheHuiXin(resp=resp_mobile)
        # 注册号
        save_data['zhuCeHao'] = self.server.getZhuCeHao(resp=resp_mobile)
        # 企业类型
        save_data['qiYeLeiXing'] = self.server.getQiYeLeiXing(resp=resp_mobile)
        # 核准日期
        save_data['heZhunRiQi'] = self.server.getHeZhunRiQi(resp=resp_pc)
        # 所在地_筛选
        save_data['suoZaiDi_ShaiXuan'] = self.server.getSuoZaiDi_Shai(resp=resp_pc)
        # 曾用名
        save_data['cengYongMing'] = self.server.getCengYongMing(resp=resp_pc)
        # 员工人数
        save_data['yuanGongRenShu'] = self.server.getYuanGongRenShu(resp=resp_pc)
        # 经营范围
        save_data['jingYingFanWei'] = self.server.getJingYingFanWei(resp=resp_pc)
        # 实缴资本
        save_data['shiJiaoZiBen'] = self.server.getShiJiaoZiBen(resp=resp_pc)
        # 成立日期
        save_data['chengLiRiQi'] = self.server.getChengLiRiQi(resp=resp_pc)
        # 纳税人识别号
        save_data['naShuiRenShiBieHao'] = self.server.getNaShuRenShiBie(resp=resp_pc)
        # 组织机构代码
        save_data['zuZhiJiGouDaiMa'] = self.server.getZuZhiJiGouDaiMa(resp=resp_pc)
        # 主营行业
        save_data['zhuYingHangYe'] = self.server.getZhuYingHangYe(resp=resp_pc)
        # 登记机关
        save_data['dengJiJiGuan'] = self.server.getDengJiJiGuan(resp=resp_pc)
        # 英文名
        save_data['yingWenMing'] = self.server.getYingWenMing(resp=resp_pc)
        # 参保人数
        save_data['canBaoRenShu'] = self.server.getCanBaoRenShu(resp=resp_pc)
        # 营业期限
        save_data['yingYeQiXian'] = self.server.getYingYeQiXian(resp=resp_pc)
        # 股东信息
        save_data['guDongXinXi'] = self.server.getGuDongXinXi(resp=resp_pc)
        # 股东及出资信息
        save_data['guDongJiChuZiXinXi'] = self.server.getGuDongJiChuZiXinXi(resp=resp_pc)
        # 获取股权变更信息
        save_data['guQuanBianGengXinXi'] = self.server.getGuQuanBianGengXinXi(resp=resp_pc)
        # 获取对外投资
        save_data['duiWaiTouZi'] = self.server.getDuiWaiTouZi(resp=resp_pc)
        # 获取主要人员
        save_data['zhuYaoRenYuan'] = self.server.getZhuYaoRenYuan(resp=resp_pc)
        # 获取分支结构
        save_data['fenZhiJiGou'] = self.server.getFenZhiJiGou(resp=resp_pc)
        # 获取变更记录
        save_data['bianGengJiLu'] = self.server.getBianGengJiLu(resp=resp_pc)
        # url
        save_data['url'] = obj
        # 生成key
        save_data['key'] = obj
        # 生成sha
        save_data['sha'] = hashlib.sha1(obj.encode('utf-8')).hexdigest()
        # 生成ss ——实体
        save_data['ss'] = '机构'
        # 生成ws ——目标网站
        save_data['ws'] = '企查查'
        # 生成clazz ——层级关系
        save_data['clazz'] = '机构_企业'
        # 生成es ——栏目名称
        save_data['es'] = '企业'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据'
        # 生成ref
        save_data['ref'] = ''
        LOGGING.info(save_data['sha'])

        self.dao.saveData(logging=LOGGING, data=save_data)

        return status
    # 获取代理
    def getProxy(self):
        while 1:
            # 获取代理IP
            proxies = proxy_utils.getAdslProxy(logging=LOGGING)
            if proxies:
                return proxies
            else:
                time.sleep(1)
                continue

    def run(self):
        redis_client = redispool_utils.createRedisPool()
        # mysql_client = mysqlpool_utils.createMysqlPool()
        while 1:
            # 获取任务
            object_list = self.dao.getObjectForRedis(logging=LOGGING, redis_client=redis_client, count=1)
            obj_list = []
            for o in object_list:
                o_url = re.sub(r"\.html", "", re.sub(r"firm", "cbase", o))
                obj_list.append(o_url)
            # obj_list = ['https://www.qichacha.com/cbase_6bc7e7ccdb755391651316a0227c059b', 'https://www.qichacha.com/cbase_52a90fffd6b3989969f67c367824e14b', 'https://www.qichacha.com/cbase_e1f3908ec9b217c8ef0a73945456e040', 'https://www.qichacha.com/cbase_b391cbd57087ae27f37a6de1f0291ba9', 'https://www.qichacha.com/cbase_f4357029e5105903b41c1be21b2612f8', 'https://www.qichacha.com/cbase_34c151d0cdc8d07f211ef2d54f4a5ac8', 'https://www.qichacha.com/cbase_50594e9682dd0c669f8c0cfd2525acfb', 'https://www.qichacha.com/cbase_503baea5942323d455678fad35de402b', 'https://www.qichacha.com/cbase_c38bed518efc278bcd0c86e946ccd9f7', 'https://www.qichacha.com/cbase_14f21065ad79476f00afe7ef5ae7100a', 'https://www.qichacha.com/cbase_c9efcd19b3adcaacf919471978a0cd76', 'https://www.qichacha.com/cbase_f467bfa5f59d3454bb1d7f0869682f94', 'https://www.qichacha.com/cbase_17c82915ce16f656b2035e763e24de55', 'https://www.qichacha.com/cbase_93ef2c54440aaff0f0591a456a9da796', 'https://www.qichacha.com/cbase_8baeaef373dd95ebf07f433bab9bde02', 'https://www.qichacha.com/cbase_5033db0e814b0f73c74e4897fc8ced5e', 'https://www.qichacha.com/cbase_500eb77509a747b0b4245f2ddc544b12', 'https://www.qichacha.com/cbase_9a18e54ba9e368a977aedb4d512ba2c7', 'https://www.qichacha.com/cbase_8577608123ed8e48725c6dfd04ff5e30', 'https://www.qichacha.com/cbase_5021389306e12f47657c85d16cdb7497', 'https://www.qichacha.com/cbase_52b0d4508c61e9d421e62246d7d8c737', 'https://www.qichacha.com/cbase_500f7636feb976626741d8753c755b2a', 'https://www.qichacha.com/cbase_10f852efc4d1771d35408d85fc840df5', 'https://www.qichacha.com/cbase_34ba423c27d25948e50d42651f1498fd', 'https://www.qichacha.com/cbase_1f8a68893c4021ed037165d3d0fd6fa3', 'https://www.qichacha.com/cbase_30c0e36697ecadd628cc8a80fe72d3e7', 'https://www.qichacha.com/cbase_608a49c58f6c6308fc091bb50e4fccfa', 'https://www.qichacha.com/cbase_03f83406b271762e4d144769841edce6', 'https://www.qichacha.com/cbase_894da435ff705796e7bf2a620cbab29b', 'https://www.qichacha.com/cbase_5015aae9112efa898774891a9827990a', 'https://www.qichacha.com/cbase_970b6ff9da20709d5c50c456e4cb5008', 'https://www.qichacha.com/cbase_503dbb7e33c9a50ce875229e336ec85c', 'https://www.qichacha.com/cbase_9a26f72f4682db9d49e0ef1676ce7bc2', 'https://www.qichacha.com/cbase_507ec840e84e10ab997ddc98d56bb306', 'https://www.qichacha.com/cbase_1528321bf93cc674865f0320bdcb29fb', 'https://www.qichacha.com/cbase_ac6f8e8021df9a11222a0d938025e46e', 'https://www.qichacha.com/cbase_10f9ab9b7e93e66869ccc6a2e15e5bd1', 'https://www.qichacha.com/cbase_2cd8f80040d45476b6c781b04d7975da', 'https://www.qichacha.com/cbase_14edc4ca38c34fa3b6f5c7a513ac3bec', 'https://www.qichacha.com/cbase_101d550cfeedb326fcb5135dbb4c7908', 'https://www.qichacha.com/cbase_0cfe461c2361473ec605377864b694cf', 'https://www.qichacha.com/cbase_e84c5f74d1048353ab3cba97c3f959a4', 'https://www.qichacha.com/cbase_d8e1756b6a8007abc4e45568415e6baf', 'https://www.qichacha.com/cbase_516922d0de318061e4ec9a70ec6b2cb5', 'https://www.qichacha.com/cbase_782c6855c29806051e82f2260eeab300', 'https://www.qichacha.com/cbase_0f60e8294ba7dbc172b98c320e7af0d8', 'https://www.qichacha.com/cbase_8b818c7382ac5c4e0184c5c1fdf5008c', 'https://www.qichacha.com/cbase_502acf0632bcacf727a2031b28eb9b3d', 'https://www.qichacha.com/cbase_03ed302e2ba42f6475cbafccda92275c', 'https://www.qichacha.com/cbase_608127697686a1c5085677810cc2fa82', 'https://www.qichacha.com/cbase_a6330f82df16f2e8f04410935322a35c', 'https://www.qichacha.com/cbase_26d7eb2089f55240dc02b72ee3895cc4', 'https://www.qichacha.com/cbase_66672ebcef4d3df68aa1cfb9cf062982', 'https://www.qichacha.com/cbase_501a17cdbb3cce6677ccb72cd596f4f3', 'https://www.qichacha.com/cbase_6668b05cdb1e3558b6c6b5a5309d1fa3', 'https://www.qichacha.com/cbase_f41cb3dcbbf83fde572d1070d17ca450', 'https://www.qichacha.com/cbase_a55b0c237a8bfdbb29feb2cfc04d3ee4', 'https://www.qichacha.com/cbase_bd18037a960effe6545a5ad133d55bd4', 'https://www.qichacha.com/cbase_34b9a7e9122345f6669b0407a076f239', 'https://www.qichacha.com/cbase_824a98aa96956f74ca5f40e4767bb375', 'https://www.qichacha.com/cbase_505f929882c3c10e141f420cfed250f4', 'https://www.qichacha.com/cbase_e84533da47d5f739e52e8cdce5ac1b09', 'https://www.qichacha.com/cbase_c0748cb4e40a03a20d5c84bd4e4eed04', 'https://www.qichacha.com/cbase_0f52db4c8be9f68777c2133b5ef9f754', 'https://www.qichacha.com/cbase_f11079730312333d44f58f42104b5878', 'https://www.qichacha.com/cbase_e84296d96212b651216f277190eed972', 'https://www.qichacha.com/cbase_f784f910afbff9d7d4e6b15993505a9e', 'https://www.qichacha.com/cbase_bd1638f88ca0f0ac7ada8f1154feb637', 'https://www.qichacha.com/cbase_eb588a65f919b00bd85c2c22cfdc5e11', 'https://www.qichacha.com/cbase_503944f4a20a778f84ff4ec419b7f744', 'https://www.qichacha.com/cbase_f41c20f72e151e1e092dc24ef384c592', 'https://www.qichacha.com/cbase_eb506d612319ab4f8eeee261791d12bd', 'https://www.qichacha.com/cbase_e8418de038c0bdb0330ff7ecb93eba10', 'https://www.qichacha.com/cbase_a6338b5d2c0c269899e0d0841ba1c113', 'https://www.qichacha.com/cbase_d579d2e4d19c4cab2db4f2595482e331', 'https://www.qichacha.com/cbase_501a594c754a3ca953423f9386d96c4c', 'https://www.qichacha.com/cbase_90acd41e5badcc6e8158a8c4b9e012cc', 'https://www.qichacha.com/cbase_8579dab3806f04ba0d82abb9ab182776', 'https://www.qichacha.com/cbase_d57e65bbbfa39c9acfb37abad1e1756e', 'https://www.qichacha.com/cbase_ee95abbe4dcd79c3110fb5ff32a85453', 'https://www.qichacha.com/cbase_cd29705985095cc80d89d59acf5a146e', 'https://www.qichacha.com/cbase_52a8af9c00c6710f72c006dcd3ff01eb', 'https://www.qichacha.com/cbase_40b43a2c9b374c20d2e7aac443a13fbf', 'https://www.qichacha.com/cbase_1134c19a611e721f1be2ec9edd99f591', 'https://www.qichacha.com/cbase_2cd54b68f91dec4d952dad6ff4bd7e25', 'https://www.qichacha.com/cbase_06a3f7a7e3dced7dd683efa725ec69d4', 'https://www.qichacha.com/cbase_600d95e4a987b6695d1ab53365e5ad6c', 'https://www.qichacha.com/cbase_df0791fc30b26cb974432049df038161', 'https://www.qichacha.com/cbase_f75c8637ec52e9f63fb99b137864ce1a', 'https://www.qichacha.com/cbase_857953dbe39ad0816dbe83b586f3ed27', 'https://www.qichacha.com/cbase_30c159a8b153b0deec08026b8f3b19af', 'https://www.qichacha.com/cbase_6025434d3b6c0ac593490dcce7fcd9d3', 'https://www.qichacha.com/cbase_d26d443aa9c7a14cc20654b16aecef4e', 'https://www.qichacha.com/cbase_50b96ab31eafe4919fed7891534260b8', 'https://www.qichacha.com/cbase_ba4e76655c38af308cd953db50183378', 'https://www.qichacha.com/cbase_2fd567cf0f09e6b86b6d778807ac8a1d', 'https://www.qichacha.com/cbase_b39db35c733901fbf9f1e66918ce1332', 'https://www.qichacha.com/cbase_a2e66aa01cb5df663588a176cc448b93', 'https://www.qichacha.com/cbase_0f55a874365a7f7e7d04d32ab84a3610', 'https://www.qichacha.com/cbase_df1099f0c4f0b566f1675a2be9c895bc']
            for obj in obj_list:
                while 1:
                    # 根据代理状态判断是否需要跟换代理
                    if self.proxies_status == 0:
                        proxies = self.proxies
                    else:
                        self.proxies = self.getProxy()
                        proxies = self.proxies
                        self.proxies = 0

                    spider_status = self.handle(obj=obj, proxies=proxies)
                    if spider_status['status'] == 1:
                        # 标记当前代理
                        proxy_utils.updateAdslProxy(proxies=proxies)
                        self.proxies = 1
                        continue
                    elif spider_status['status'] == 0:

                        self.proxies = 0
                        break

                    else:
                        # 标记当前代理
                        proxy_utils.updateAdslProxy(proxies=proxies)
                        self.proxies = 1
                        break

            #     break
            #
            # break


if __name__ == '__main__':
    cookie = 'null'
    user_agent = create_ua_utils.get_ua()
    main_obj = SpiderMain(cookie=cookie, user_agent=user_agent)
    main_obj.run()