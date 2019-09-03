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
REDIS_CATALOG = 'eng_catalog' # redis列表种子任务表
REDIS_CATALOG_LOCK = 'eng_catalog_lock' # redis列表种子分布式锁名

REDIS_PROFILE = 'eng_profile' # redis列表种子任务表
REDIS_PROFILE_LOCK = 'eng_profile_lock' # redis列表种子分布式锁名

MYSQL_STANTARD = 'job_standard' # Mysql标准任务表
REDIS_STANTARD = 'eng_standard' # Redis标准任务表
REDIS_STANTARD_LOCK = 'eng_standard_lock' # Redis标准分布式锁名

MYSQL_INSTITUTE = 'job_institute' # Mysql机构任务表
REDIS_INSTITUTE = 'eng_institute' # Redis机构任务表
REDIS_INSTITUTE_LOCK = 'eng_institute_lock' # Redis机构分布式锁名

MYSQL_IMG = 'job_img' # Mysql图片任务表
REDIS_IMG = 'eng_img' # Redis图片任务表
REDIS_IMG_LOCK = 'eng_img_lock' # Redis图片分布式锁名

# ----------------------------
# 进程数配置
# ----------------------------
DATA_SCRIPT_PROCESS = 4 # 数据爬虫进程数