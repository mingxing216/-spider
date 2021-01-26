# -*-coding:utf-8-*-

'''
线上环境配置参数
'''

# 下载延时
DOWNLOAD_MIN_DELAY = 0.2
DOWNLOAD_MAX_DELAY = 0.5

# Mysql
DB_HOST='192.168.10.92'
DB_PORT=3306
DB_USER='spider'
DB_PASS='spider'
DB_NAME='spider'
# DB_POOL_NUMBER=10 # 连接池内连接默认数量

# redis
REDIS_HOST='192.168.10.92'
REDIS_PORT=6379
REDIS_PASSWORD='spider'
# REDIS_POOL_MAX_NUMBER=10 # redis链接池最大连接数

# MongoDB
M_HOST='127.0.0.1'
M_PORT=27017

# 若快打码================================================
r_username='15711294367'
r_password='rockerfm520'
r_soft_id=116272
r_soft_key='c4f5ffd82a6f4cfeafdd8c062c0358ca'

# 橙子短验API参数==========================================
OrangeAPI_uid='y3138359'
OrangeAPI_pwd='3138359'
Orange_Pid=46808

# =================== 存储 ========================
# hbase存储爬虫输出数据
SAVE_HBASE_DATA_URL='http://192.168.10.187:8090/hbaseserver/dat/saveStructuredData?'
# hbase存储爬虫输出多媒体文件
SAVE_HBASE_MEDIA_URL='http://192.168.10.187:8090/hbaseserver/dat/saveMediaData?'

# ================== 读取 =====================
# hbase读取实体数据
GET_HBASE_DATA_URL = 'http://192.168.10.187:8090/hbaseserver/dat/getStructuredData?sha={}&ss={}'
# hbase读取多媒体文件
GET_HBASE_MEDIA_URL = 'http://192.168.10.187:8090/hbaseserver/dat/getMediaData?sha={}&type={}'

# ==================《代理池》==================
# # ADSL获取代理接口
# GET_PROXY_API = "http://47.104.235.235:8000/random"
# 获取代理接口
GET_PROXY_API = "http://192.168.10.93:5000/proxy/get?ws={}&p={}&ut={}"
# 代理权重设置最大接口
ADD_PROXY_API = "http://192.168.10.93:5000/proxy/add?ip={}&p={}&rt={}"
# 代理释放,修改权重接口
RELEASE_PROXY_API = "http://192.168.10.93:5000/proxy/release?ip={}&result={}"

# ==================《用户cookie池》==================
# 获取cookie接口
GET_COOKIE_API = "http://60.195.249.95:5100/random/min"
# cookie增加分数接口
INC_COOKIE_API = "http://60.195.249.95:5100/increase?username={}"
# cookie增加分数接口
MAX_COOKIE_API = "http://60.195.249.95:5100/increase/max?username={}"
# cookie减少分数接口
DEC_COOKIE_API = "http://60.195.249.95:5100/decrease?username={}"


# # 获取代理接口
# GET_PROXY_API = "http://proxyserver.onecooo.com:5000/get-proxy"
# # 代理状态更新接口
# UPDATE_PROXY_API = "http://proxyserver.onecooo.com:5000/update-proxy"
# # 删除代理接口
# DELETE_PROXY_API = "http://proxyserver.onecooo.com:5000/delete-proxy"

# mysql数据库存储流媒体文件url的表名
MEDIA_TABLE = 'ss_media'

# 已抓取数据记录总表
DATA_VOLUME_TOTAL_TABLE = 'data_volume_total'
# 每日已抓取数据记录表
DATA_VOLUME_DAY_TABLE = 'data_volume_day'
# 数据量表
DATA_NUMBER_TOTAL_TABLE = 'data_number_total'
# 爬虫列表
SPIDER_TABLE = 'ss_spider'
# 任务表
TASK_TABLE = 'ss_task'


# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'