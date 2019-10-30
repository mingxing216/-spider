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
REDIS_CATALOG = 'my_catalog' # redis列表种子任务表
REDIS_CATALOG_LOCK = 'my_catalog_lock' # redis列表种子分布式锁名


MYSQL_STANDARD = 'job_standard' # Mysql标准任务表
REDIS_STANDARD = 'my_standard' # Redis标准任务表
REDIS_STANDARD_LOCK = 'my_standard_lock' # Redis标准分布式锁名

MYSQL_PRICE = 'job_price' # Mysql价格任务表
REDIS_PRICE = 'my_price' # Redis价格任务表
REDIS_PRICE_LOCK = 'my_price_lock' # Redis价格分布式锁名

MYSQL_INSTITUTE = 'job_institute' # Mysql机构任务表
REDIS_INSTITUTE = 'my_institute' # Redis机构任务表
REDIS_INSTITUTE_LOCK = 'my_institute_lock' # Redis机构分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'my_document' # Redis文档任务表
REDIS_DOCUMENT_LOCK = 'my_document_lock' # Redis文档分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数