# -*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE ='http' # 代理IP协议种类
TIMEOUT = 10 # 请求超时
COUNTRY = 1 # 代理IP所属国家
CITY = 0 # 代理IP所属城市
MYSQL_POOL_NUMBER = 1 # Mysql连接池数量
REDIS_POOL_NUMBER = 1 # Redis连接池数量


# ----------------------------
# musql数据表配置/redis数据表配置/redis锁配置
# ----------------------------
# 发明公开/发明授权/外观专利/实用新型
REDIS_CATEGORY = 'zhiwang_category' # Redis发明公开任务表
REDIS_CATEGORY_LOCK = 'zhiwang_category_lock' # Redis发明公开分布式锁名

REDIS_SQ_CATEGORY = 'zhiwang_sq_category' # Redis发明授权任务表
REDIS_SQ_CATEGORY_LOCK = 'zhiwang_sq_category_lock' # Redis发明授权分布式锁名

REDIS_WG_CATEGORY = 'zhiwang_wg_category' # Redis外观专利任务表
REDIS_WG_CATEGORY_LOCK = 'zhiwang_wg_category_lock' # Redis外观专利分布式锁名

REDIS_XX_CATEGORY = 'zhiwang_xx_category' # Redis实用新型任务表
REDIS_XX_CATEGORY_LOCK = 'zhiwang_xx_category_lock' # Redis实用新型分布式锁名


MYSQL_PATENT = 'job_patent' # Mysql任务表

REDIS_FM_PATENT = 'zhiwang_fm_patent' # Redis发明公开任务表
REDIS_FM_PATENT_LOCK = 'zhiwang_fm_patent_lock' # Redis发明公开分布式锁名

REDIS_SQ_PATENT = 'zhiwang_sq_patent' # Redis发明授权任务表
REDIS_SQ_PATENT_LOCK = 'zhiwang_sq_patent_lock' # Redis发明授权分布式锁名

REDIS_WG_PATENT = 'zhiwang_wg_patent' # Redis外观专利任务表
REDIS_WG_PATENT_LOCK = 'zhiwang_wg_patent_lock' # Redis外观专利分布式锁名

REDIS_XX_PATENT = 'zhiwang_xx_patent' # Redis实用新型任务表
REDIS_XX_PATENT_LOCK = 'zhiwang_xx_patent_lock' # Redis实用新型分布式锁名


MYSQL_ANNOUNCEMENT = 'job_announcement' # Mysql任务表
REDIS_ANNOUNCEMENT = 'zhiwang_announcement' # Redis任务表
REDIS_ANNOUNCEMENT_LOCK = 'zhiwang_announcement_lock' # Redis分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数