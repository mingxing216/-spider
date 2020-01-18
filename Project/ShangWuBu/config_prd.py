# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = None # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------
# 中国商务法规
REDIS_SHANGWUBU_FAGUI = 'shangwubu_fagui_category' # Redis分类任务表
REDIS_SHANGWUBU_FAGUI_LOCK = 'shangwubu_fagui_category_lock' # Redis分类分布式锁名

# 中外条约
REDIS_SHANGWUBU_TIAOYUE = 'shangwubu_tiaoyue_category' # Redis分类任务表
REDIS_SHANGWUBU_TIAOYUE_LOCK = 'shangwubu_tiaoyue_category_lock' # Redis分类分布式锁名

# 法律
MYSQL_LAW = 'job_law' # Mysql法律任务表

REDIS_FAGUI_LAW = 'shangwubu_fagui_law' # Redis法规任务表
REDIS_FAGUI_LAW_LOCK = 'shangwubu_fagui_law_lock' # Redis法规分布式锁名

REDIS_TIAOYUE_LAW = 'shangwubu_tiaoyue_law' # Redis条约任务表
REDIS_TIAOYUE_LAW_LOCK = 'shangwubu_tiaoyue_law_lock' # Redis条约分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数
