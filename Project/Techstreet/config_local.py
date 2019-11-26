#-*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = 'http' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 0 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# mysql表名配置/redis表名配置
# ----------------------------
REDIS_CATALOG = 'tech_catalog' # redis列表种子任务表
REDIS_CATALOG_LOCK = 'tech_catalog_lock' # redis列表种子分布式锁名


MYSQL_STANDARD = 'job_standard' # Mysql标准任务表
REDIS_STANDARD = 'tech_standard' # Redis标准任务表
REDIS_STANDARD_LOCK = 'tech_standard_lock' # Redis标准分布式锁名

MYSQL_PRICE = 'job_price' # Mysql价格任务表
REDIS_PRICE = 'tech_price' # Redis价格任务表
REDIS_PRICE_LOCK = 'tech_price_lock' # Redis价格分布式锁名

MYSQL_INSTITUTE = 'job_institute' # Mysql机构任务表
REDIS_INSTITUTE = 'tech_institute' # Redis机构任务表
REDIS_INSTITUTE_LOCK = 'tech_institute_lock' # Redis机构分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'tech_document' # Redis文档任务表
REDIS_DOCUMENT_LOCK = 'tech_document_lock' # Redis文档分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数