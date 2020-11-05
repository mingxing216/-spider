# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

# 是否需要代理IP，
# 需要（任何能返回True的值，一般写http）
# 不需要（None)
PROXY_TYPE = 'http'
STREAM = False # 是否要流式下载
TIMEOUT = (5, 10) # 请求超时(连接超时、读取超时)
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 10 # Mysql连接池数量
REDIS_POOL_NUMBER = 5 # Redis连接池数量
MAX_QUEUE_REDIS = 2000 # redis最大队列数量

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

MYSQL_TEST = 'job_test' # Mysql论文任务表
REDIS_ZIRANKEXUE_TEST = 'zirankexue_test' # Redis论文任务表
REDIS_ZIRANKEXUE_TEST_LOCK = 'zirankexue_test_lock' # Redis论文分布式锁名

# MYSQL_TEST = 'job_paper_temp' # Mysql论文任务表
# REDIS_ZIRANKEXUE_TEST = 'zirankexue_paper_temp' # Redis论文任务表
# REDIS_ZIRANKEXUE_TEST_LOCK = 'zirankexue_paper_temp_lock' # Redis论文分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
PROCESS_NUM = 4 # 数据爬虫进程数
THREAD_NUM = 8 # 数据爬虫线程数
