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
# 中国商务法规/中外条约
REDIS_SHANGWUBU_CATEGORY = 'shangwubu_category' # Redis分类任务表
REDIS_SHANGWUBU_CATEGORY_LOCK = 'shangwubu_category_lock' # Redis分类分布式锁名

MYSQL_LAW = 'job_law' # Mysql报告任务表
REDIS_SHANGWUBU_LAW = 'shangwubu_law' # Redis报告任务表
REDIS_SHANGWUBU_LAW_LOCK = 'shangwubu_law_lock' # Redis报告分布式锁名


# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数
