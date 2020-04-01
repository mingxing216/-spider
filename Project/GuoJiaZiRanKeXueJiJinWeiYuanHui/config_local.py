# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = 'http' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量

# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------
# 期刊论文
REDIS_ZIRANKEXUE_CATALOG = 'zirankexue_catalog' # Redis分类任务表
REDIS_ZIRANKEXUE_CATALOG_LOCK = 'zirankexue_catalog_lock' # Redis分类分布式锁名


MYSQL_PAPER = 'job_paper' # Mysql论文任务表
REDIS_ZIRANKEXUE_PAPER = 'zirankexue_paper' # Redis论文任务表
REDIS_ZIRANKEXUE_PAPER_LOCK = 'zirankexue_paper_lock' # Redis论文分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_ZIRANKEXUE_DOCUMENT = 'zirankexue_document' # Redis文档任务表
REDIS_ZIRANKEXUE_DOCUMENT_LOCK = 'zirankexue_document_lock' # Redis文档分布式锁名


# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数
