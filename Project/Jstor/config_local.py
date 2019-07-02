#-*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE='https' # 代理IP协议种类
TIMEOUT=10 # 请求超时
COUNTRY=1 # 代理IP所属国家
CITY=0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# mysql表名配置
# ----------------------------
MYSQL_PAPER = 'job_paper' # Mysql论文任务表
REDIS_PAPER = 'job_paper' # Redis论文任务表

# ----------------------------
# 锁配置
# ----------------------------
REDIS_PAPER_LOCK = 'job_paper_lock' # Redis分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 8 # 数据爬虫进程数