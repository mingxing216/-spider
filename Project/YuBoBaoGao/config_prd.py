# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE ='http' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------
# 行业研究报告
REDIS_YUBO_CATEGORY = 'yubo_category' # Redis分类任务表
REDIS_YUBO_CATEGORY_LOCK = 'yubo_category_lock' # Redis分类分布式锁名


MYSQL_REPORT = 'job_report' # Mysql报告任务表
REDIS_YUBO_REPORT = 'yubo_report' # Redis报告任务表
REDIS_YUBO_REPORT_LOCK = 'yubo_report_lock' # Redis报告分布式锁名

MYSQL_PRICE = 'job_price' # Mysql价格任务表
REDIS_YUBO_PRICE = 'yubo_price' # Redis价格任务表
REDIS_YUBO_PRICE_LOCK = 'yubo_price_lock' # Redis价格分布式锁名


# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数
