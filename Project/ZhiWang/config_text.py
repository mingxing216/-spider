# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE='http' # 代理IP协议种类
TIMEOUT=10 # 请求超时
COUNTRY=1 # 代理IP所属国家
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量


# ----------------------------
# 数据表配置
# ----------------------------
MYSQL_TASK = 'ss_zhiwang_zhuanli_url' # Mysql任务表
REDIS_TASK = 'ss_zhiwang_zhuanli_url' # Redis任务表


# ----------------------------
# 锁配置
# ----------------------------
REDIS_TASK_LOCK = 'ss_zhiwang_zhuanli_url_lock' # Redis分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 8 # 数据爬虫进程数


