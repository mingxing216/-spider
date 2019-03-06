#-*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------
# 代理IP协议种类
PROXY_TYPE='http'
# 代理重复获取次数
UPDATE_PROXY_FREQUENCY=8
# 同IP重复请求次数
RETRY=3
# 请求超时
TIMEOUT=10
# 代理IP所属国家
COUNTRY=1


# ----------------------------
# mysql表名配置
# ----------------------------
# 已抓任务存放表(用于抓取去重)
MYSQL_REMOVAL = 'ss_zhiwang_removal'
# 期刊任务表
MYSQL_QIKAN = 'ss_zhiwang_qikan'
# 论文任务表
MYSQL_LUNWEN = 'ss_zhiwang_lunwen'
# 作者任务表
MYSQL_ZUOZHE = 'ss_zhiwang_zuozhe'
# 机构任务表
MYSQL_JIGOU = 'ss_zhiwang_jigou'


# ----------------------------
# redis队列配置
# ----------------------------
# 队列内容最大数
REDIS_MAX = 2000
# 队列内容最小数
REDIS_MIN = 0

# 期刊论文_期刊队列名
REDIS_QIKANLUNWEN_QIKAN = 'ss_qikanlunwen_qikan'
# 会议论文_期刊队列名
REDIS_HUIYILUNWEN_QIKAN = 'ss_huiyilunwen_qikan'
# 学位论文_期刊队列
REDIS_XUEWEILUNWEN_QIKAN = 'ss_xueweilunwen_qikan'

# 期刊论文_论文队列名
REDIS_QIKANLUNWEN_LUNWEN = 'ss_qikanlunwen_lunwen'
# 期刊论文_论文队列分布式锁名
REDIS_QIKANLUNWEN_LUNWEN_LOCK = 'ss_qikanlunwen_lunwen_lock'
# 会议论文_论文队列名
REDIS_HUIYILUNWEN_LUNWEN = 'ss_huiyilunwen_lunwen'
# 会议论文_论文队列分布式锁名
REDIS_HUIYILUNWEN_LUNWEN_LOCK = 'ss_huiyilunwen_lunwen_lock'
# 学位论文_论文队列名
REDIS_XUEWEILUNWEN_LUNWEN = 'ss_xueweilunwen_lunwen'
# 学位论文_论文队列分布式锁名
REDIS_XUEWEILUNWEN_LUNWEN_LOCK = 'ss_xueweilunwen_lunwen_lock'


# 机构队列名
REDIS_JIGOU = 'ss_zhiwang_jigou'
# 机构队列分布式锁名
REDIS_JIGOU_LOCK = 'ss_zhiwang_jigou_lock'
# 作者队列名
REDIS_ZUOZHE = 'ss_zhiwang_zuozhe'
# 作者队列分布式锁名
REDIS_ZUOZHE_LOCK = 'ss_zhiwang_zuozhe_lock'


# ----------------------------
# 数据种类配置
# ----------------------------
# qiKanLunWen_qiKan_main.py --> 数据输出种类
QIKANLUNWEN_QIKAN_MAIN = 'qikan'
# huiYiLunWen_qiKan_main.py --> 数据输出种类
HUIYILUNWEN_QIKAN_MAIN = 'huiyi'
# xueWeiLunWen_qiKan_main.py --> 数据输出种类
XUEWEILUNWEN_QIKAN_MAIN = 'xuewei'

# qiKanLunWen_lunWen_main.py --> 数据输出种类
QIKANLUNWEN_LUNWEN_MAIN = 'qikan'
# huiYiLunWen_lunWenData_main.py --> 数据输出种类
HUIYILUNWEN_LUNWEN_MAIN = 'huiyi'
# xueWeiLunWen_lunWen_main.py --> 数据输出种类
XUEWEILUNWEN_LUNWEN_MAIN = 'xuewei'


# ----------------------------
# 程序进程数配置
# ----------------------------
# 期刊论文_期刊任务
QIKANLUNWEN_QIKANRENWU_PROCESS_NUMBER = 1 # 不可更改
# 会议论文_期刊任务
HUIYILUNWEN_QIKANRENWU_PROCESS_NUMBER = 1 # 不可更改
# 学位论文_期刊任务
XUEWEILUNWEN_QIKANRENWU_PROCESS_NUMBER = 1 # 不可更改

# 期刊论文_论文任务
QIKANLUNWEN_LUNWENRENWU_PROCESS_NUMBER = 1 # 不可更改
# 会议论文_论文任务
HUIYILUNWEN_LUNWENRENWU_PROCESS_NUMBER = 1 # 不可更改
# 学位论文_论文任务
XUEWEILUNWEN_LUNWENRENWU_PROCESS_NUMBER = 1 # 不可更改

# 期刊论文_论文数据
QIKANLUNWEN_LUNWENDATA_PROCESS_NUMBER = 8
# 会议论文_论文数据
HUIYILUNWEN_LUNWENDATA_PROCESS_NUMBER = 8
# 学位论文_论文数据
XUEWEILUNWEN_LUNWENDATA_PROCESS_NUMBER = 8

# 知网论文_机构数据
ZHIWANGLUNWEN_JIGOUDATA_PROCESS_NUMBER = 8
# 知网论文_作者数据
ZHIWANGLUNWEN_ZUOZHEDATA_PROCESS_NUMBER = 8
# 知网论文_会议数据
ZHIWANGLUNWEN_HUIYIDATA_PROCESS_NUMBER = 1 # 不可更改
# 知网论文_期刊数据
ZHIWANGLUNWEN_QIKANDATA_PROCESS_NUMBER = 1 # 不可更改
# 知网论文_文集数据
ZHIWANGLUNWEN_WENJIDATA_PROCESS_NUMBER = 1 # 不可更改

