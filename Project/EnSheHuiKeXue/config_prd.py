# -*- coding:utf-8 -*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE = 'http'  # 代理IP协议种类
STREAM = False  # 是否要流式下载
TIMEOUT = (10, 30)  # 请求超时(连接超时、读取超时)
COUNTRY = 1  # 代理IP所属国家
CITY = 0  # 代理IP所属城市
MYSQL_POOL_NUMBER = 5  # Mysql连接池数量
REDIS_POOL_NUMBER = 5  # Redis连接池数量
MAX_QUEUE_REDIS = 2000  # redis最大队列数量

# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------

# 期刊列表
REDIS_ZHEXUESHEHUIKEXUE_CATALOG = 'zhexueshehuikexue_catalog'  # Redis分类任务表
REDIS_ZHEXUESHEHUIKEXUE_CATALOG_LOCK = 'zhexueshehuikexue_catalog_lock'  # Redis分类分布式锁名

REDIS_ZHEXUESHEHUIKEXUE_PAGE_CATALOG = 'zhexueshehuikexue_page_catalog'  # Redis分类任务表
REDIS_ZHEXUESHEHUIKEXUE_PAGE_CATALOG_LOCK = 'zhexueshehuikexue_page_catalog_lock'  # Redis分类分布式锁名

MYSQL_MAGAZINE = 'job_magazine'  # Mysql期刊任务表
REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE = 'zhexueshehuikexue_magazine'  # Redis期刊任务表
REDIS_ZHEXUESHEHUIKEXUE_MAGAZINE_LOCK = 'zhexueshehuikexue_magazine_lock'  # Redis期刊分布式锁名

MYSQL_PAPER = 'job_paper_sheke'  # Mysql论文任务表
REDIS_ZHEXUESHEHUIKEXUE_PAPER = 'zhexueshehuikexue_paper'  # Redis论文任务表
REDIS_ZHEXUESHEHUIKEXUE_PAPER_LOCK = 'zhexueshehuikexue_paper_lock'  # Redis论文分布式锁名

MYSQL_DOCUMENT = 'job_document'  # Mysql文档任务表
REDIS_ZHEXUESHEHUIKEXUE_DOCUMENT = 'zhexueshehuikexue_document'  # Redis文档任务表
REDIS_ZHEXUESHEHUIKEXUE_DOCUMENT_LOCK = 'zhexueshehuikexue_document_lock'  # Redis文档分布式锁名

MYSQL_TEST = 'job_test'  # Mysql论文任务表
REDIS_ZHEXUESHEHUIKEXUE_TEST = 'zhexueshehuikexue_paper_test'  # Redis论文任务表
REDIS_ZHEXUESHEHUIKEXUE_TEST_LOCK = 'zhexueshehuikexue_paper_test_lock'  # Redis论文分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
PROCESS_NUM = 1  # 数据爬虫进程数
THREAD_NUM = 1  # 数据爬虫线程数
