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
# mysql表名配置/redis表名配置
# ----------------------------
REDIS_YEAR = 'job_year' # redis年任务表

MYSQL_PAPER = 'job_paper' # Mysql论文任务表
REDIS_PAPER = 'job_paper' # Redis论文任务表

MYSQL_MAGAZINE = 'job_magazine' # Mysql期刊任务表
REDIS_MAGAZINE = 'job_magazine' # Redis期刊任务表

MYSQL_DOCUMENT = 'job_document' # Mysql文档任务表
REDIS_DOCUMENT = 'job_document' # Redis文档任务表

MYSQL_IMG = 'job_img' # Mysql图片任务表
REDIS_IMG = 'job_img' # Redis图片任务表

# ----------------------------
# 锁配置
# ----------------------------
REDIS_YEAR_LOCK = 'job_year_lock' # redis年分布式锁名

REDIS_PAPER_LOCK = 'job_paper_lock' # Redis论文分布式锁名
REDIS_MAGAZINE_LOCK = 'job_magazine_lock' # Redis期刊分布式锁名
REDIS_DOCUMENT_LOCK = 'job_document_lock' # Redis文档分布式锁名
REDIS_IMG_LOCK = 'job_img_lock' # Redis图片分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 8 # 数据爬虫进程数