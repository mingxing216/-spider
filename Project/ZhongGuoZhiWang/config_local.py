# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE ='https' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量


# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------
MYSQL_PATENT = 'job_patent' # Mysql任务表
REDIS_PATENT = 'zhiwnag_patent' # Redis任务表
REDIS_PATENT_LOCK = 'zhiwnag_patent_lock' # Redis分布式锁名

MYSQL_ANNOUNCEMENT = 'job_announcement' # Mysql任务表
REDIS_ANNOUNCEMENT = 'zhiwnag_announcement' # Redis任务表
REDIS_ANNOUNCEMENT_LOCK = 'zhiwnag_announcement_lock' # Redis分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数


