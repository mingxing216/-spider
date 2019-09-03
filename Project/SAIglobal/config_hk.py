#-*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = 'adsl' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 'HK' # 代理IP所属国家
CITY = 'HK' # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# mysql表名配置/redis表名配置
# ----------------------------
REDIS_CATALOG = 'sai_catalog' # redis列表种子任务表
REDIS_CATALOG_LOCK = 'sai_catalog_lock' # redis列表种子分布式锁名


MYSQL_STANTARD = 'job_standard' # Mysql标准任务表
REDIS_STANTARD = 'sai_standard' # Redis标准任务表
REDIS_STANTARD_LOCK = 'sai_standard_lock' # Redis标准分布式锁名

MYSQL_INSTITUTE = 'job_institute' # Mysql机构任务表
REDIS_INSTITUTE = 'sai_institute' # Redis机构任务表
REDIS_INSTITUTE_LOCK = 'sai_institute_lock' # Redis机构分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'sai_document' # Redis文档任务表
REDIS_DOCUMENT_LOCK = 'sai_document_lock' # Redis文档分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数