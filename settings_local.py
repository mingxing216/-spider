#-*-coding:utf-8-*-

'''
本地环境配置参数
'''

# Mysql
DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER='root'
DB_PASS='rockerfm520'
DB_NAME='spider'
DB_POOL_MIN_NUMBER=10 # 连接池空闲链接最小数目
DB_POOL_MAX_NUMBER=10 # 连接池空闲链接最大数据
DB_POOL_MAX_CONNECT=10 # 连接池最大连接数

# redis
REDIS_HOST='127.0.0.1'
REDIS_PORT=6379
REDIS_PASSWORD='rockerfm520'
REDIS_POOL_MAX_NUMBER=10 # redis链接池最大连接数

# MongoDB
M_HOST='127.0.0.1'
M_PORT=27017


# 线上芝麻代理套餐==========================================

ZHIMA_SETMEAL=32716 # 芝麻代理套餐号
REDIS_PROXY_KEY='zhimaProxyPool' # redis中保存socks代理IP的列表名
REDIS_PROXY_NUMBER=2 # redis中保存socks5代理IP的数量
REDIS_PROXY_KEY_HTTP='zhimaProxyPoolHttp' # redis中保存http代理的列表名
REDIS_PROXY_NUMBER_HTTP=2 # redis中保存http代理ip的数量
REDIS_PROXY_KEY_HTTPS='zhimaProxyPoolHttps' # redis中保存https代理的列表名
REDIS_PROXY_NUMBER_HTTPS=2 # redis中保存https代理ip的数量

# 芝麻套餐余量查询参数
SETMEALNEEK=54871
SETMEALAPPKEY='fd2f243b621fd4fef564c5a80a6c1a65'
AC=ZHIMA_SETMEAL

# =======================================================

# 知网期刊爬虫最大进程数
ZHIWANG_PERIODOCAL_SPIDER_PROCESS = 4
# 知网论文作者机构爬虫最大进程数
ZHIWANG_JIGOU_SPIDER_PROCESS = 1


# 若快打码================================================
r_username='15711294367'
r_password='rockerfm520'
r_soft_id=116272
r_soft_key='c4f5ffd82a6f4cfeafdd8c062c0358ca'


# 橙子短验API参数==========================================
OrangeAPI_uid='y3138359'
OrangeAPI_pwd='3138359'
Orange_Pid=46808

# ======================================================

# hbase存储爬虫输出数据
SpiderDataSaveUrl='http://60.195.249.89:8086/dataserver/dat/saveStructuredData?'
# hbase存储爬虫输出多媒体文件
SpiderMediaSaveUrl='http://60.195.249.89:8086/dataserver/dat/saveMediaData?'

# ==================《万方专利》======================

# 万方专利任务生成程序最大进程数
WANFANG_PATENT_URL_SPIDER_PROCESS = 4
# 完场专利数据抓取程序最大进程数
WANFANG_PATENT_DATA_SPIDER_PROCESS = 4

# ==================《新华网》======================

# 新华网数据抓取程序最大进程数
XINHUA_NEWS_DATA_SPIDER_PROCESS = 4

# ==================《58同城企业名录》====================

# 58同城企业名目爬虫最大进程数
COMPANY_TITLE_FOR_58TONGCHENG = 4

# ==================《长效代理》====================

# redis长效代理IP集合名
LANG_PROXY_KEY = 'lang_proxy_pool'

# ==================《adsl代理池》==================

# 获取代理接口
GET_PROXY_API = "http://60.195.249.95:5000/get-proxy"
# 代理状态更新接口
UPDATE_PROXY_API = "http://60.195.249.95:5000/update-proxy"



# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'
