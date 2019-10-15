# -*-coding:utf-8-*-
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
# mysql表名配置/redis表名配置/redis锁配置
# ----------------------------
REDIS_CATALOG = 'ieee_catalog' # Redis论文列表页任务表
REDIS_CATALOG_LOCK = 'ieee_catalog_lock' # Redis论文列表页分布式锁名

MYSQL_PAPER = 'job_paper' # Mysql论文任务表
REDIS_PAPER = 'ieee_paper' # Redis会议论文任务表
REDIS_PAPER_LOCK = 'ieee_paper_lock' # Redis论文分布式锁名
REDIS_QIKAN_PAPER = 'ieee_qikan_paper' # Redis期刊论文任务表
REDIS_QIKAN_PAPER_LOCK = 'ieee_qikan_paper_lock' # Redis论文分布式锁名

MYSQL_MAGAZINE = 'job_magazine' # Mysql期刊任务表
REDIS_MAGAZINE = 'ieee_magazine' # Redis期刊任务表
REDIS_MAGAZINE_LOCK = 'ieee_magazine_lock' # Redis期刊分布式锁名

MYSQL_ACTIVITY = 'job_activity' # Mysql会议任务表
REDIS_ACTIVITY = 'ieee_activity' # Redis会议任务表
REDIS_ACTIVITY_LOCK = 'ieee_activity_lock' # Redis会议分布式锁名

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'ieee_document' # Redis文档任务表
REDIS_DOCUMENT_LOCK = 'ieee_document_lock' # Redis文档分布式锁名

MYSQL_PEOPLE = 'job_people' # Mysql期刊任务表
REDIS_PEOPLE = 'ieee_people' # Redis期刊任务表
REDIS_PEOPLE_LOCK = 'ieee_people_lock' # Redis期刊分布式锁名

MYSQL_IMG = 'job_img' # Mysql图片任务表
REDIS_IMG = 'ieee_img' # Redis图片任务表
REDIS_IMG_LOCK = 'ieee_img_lock' # Redis图片分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数