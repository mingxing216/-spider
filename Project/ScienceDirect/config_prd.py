# -*- coding:utf-8 -*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_ENABLED = False  # 是否使用代理
STREAM = False  # 是否要流式下载
TIMEOUT = (10, 30)  # 请求超时(连接超时、读取超时)
MYSQL_POOL_NUMBER = 10  # Mysql连接池数量
REDIS_POOL_NUMBER = 10  # Redis连接池数量
MAX_QUEUE_REDIS = 2000  # redis最大队列数量

# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------

# 期刊列表
REDIS_SCIENCEDIRECT_CATALOG = 'sciencedirect_catalog'  # Redis分类任务表
REDIS_SCIENCEDIRECT_CATALOG_LOCK = 'sciencedirect_catalog_lock'  # Redis分类分布式锁名

# 临时期刊列表
REDIS_SCIENCEDIRECT_CATALOG_TEMP = 'sciencedirect_catalog_temp'  # Redis分类任务表
REDIS_SCIENCEDIRECT_CATALOG_TEMP_LOCK = 'sciencedirect_catalog_temp_lock'  # Redis分类分布式锁名

REDIS_SCIENCEDIRECT_PAGE_CATALOG = 'sciencedirect_page_catalog'  # Redis分类任务表
REDIS_SCIENCEDIRECT_PAGE_CATALOG_LOCK = 'sciencedirect_page_catalog_lock'  # Redis分类分布式锁名

MYSQL_MAGAZINE = 'job_magazine'  # Mysql期刊任务表
REDIS_SCIENCEDIRECT_MAGAZINE = 'sciencedirect_magazine'  # Redis期刊任务表
REDIS_SCIENCEDIRECT_MAGAZINE_LOCK = 'sciencedirect_magazine_lock'  # Redis期刊分布式锁名

MYSQL_PAPER = 'job_paper'  # Mysql论文任务表
REDIS_SCIENCEDIRECT_PAPER = 'sciencedirect_paper'  # Redis论文任务表
REDIS_SCIENCEDIRECT_PAPER_LOCK = 'sciencedirect_paper_lock'  # Redis论文分布式锁名

MYSQL_DOCUMENT = 'job_document'  # Mysql文档任务表
REDIS_SCIENCEDIRECT_DOCUMENT = 'sciencedirect_document'  # Redis文档任务表
REDIS_SCIENCEDIRECT_DOCUMENT_LOCK = 'sciencedirect_document_lock'  # Redis文档分布式锁名

MYSQL_TEST = 'job_test'  # Mysql论文任务表
REDIS_SCIENCEDIRECT_TEST = 'sciencedirect_paper_test'  # Redis论文任务表
REDIS_SCIENCEDIRECT_TEST_LOCK = 'sciencedirect_paper_test_lock'  # Redis论文分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
PROCESS_NUM = 1  # 数据爬虫进程数
THREAD_NUM = 1  # 数据爬虫线程数
