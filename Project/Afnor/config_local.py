# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = 'https' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# mysql表名配置/redis表名配置
# ----------------------------
REDIS_CATALOG = 'afnor_catalog' # redis列表种子任务表
REDIS_CATALOG_LOCK = 'afnor_catalog_lock' # redis列表种子分布式锁名


MYSQL_STANDARD = 'job_standard' # Mysql标准任务表
REDIS_STANDARD = 'afnor_standard' # Redis标准任务表
REDIS_STANDARD_LOCK = 'afnor_standard_lock' # Redis标准分布式锁名

MYSQL_PRICE = 'job_price' # Mysql价格任务表
REDIS_PRICE = 'afnor_price' # Redis价格任务表
REDIS_PRICE_LOCK = 'afnor_price_lock' # Redis价格分布式锁名

MYSQL_INSTITUTE = 'job_institute' # Mysql机构任务表
REDIS_INSTITUTE = 'afnor_institute' # Redis机构任务表
REDIS_INSTITUTE_LOCK = 'afnor_institute_lock' # Redis机构分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'afnor_document' # Redis文档任务表
REDIS_DOCUMENT_LOCK = 'afnor_document_lock' # Redis文档分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数