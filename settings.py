#-*-coding:utf-8-*-

'''
本地环境配置参数
'''

# 下载延时
DOWNLOAD_MIN_DELAY = 0.2
DOWNLOAD_MAX_DELAY = 0.5

# Mysql
DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER='root'
DB_PASS='onecooo'
DB_NAME='spider'
# DB_POOL_NUMBER=10 # 连接池内连接默认数量

# redis
REDIS_HOST='127.0.0.1'
REDIS_PORT=6379
REDIS_PASSWORD='onecooo'
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

# ======================================================
# hbase存储爬虫输出数据
SpiderDataSaveUrl='http://60.195.249.89:8086/dataserver/dat/saveStructuredData?'
# hbase存储爬虫输出多媒体文件
SpiderMediaSaveUrl='http://60.195.249.89:8086/dataserver/dat/saveMediaData?'

# ==================《adsl代理池》==================
# 获取代理接口
GET_PROXY_API = "http://47.244.189.91/get-proxy"
# 代理状态更新接口
UPDATE_PROXY_API = "http://47.244.189.91/update-proxy"
# 删除代理接口
DELETE_PROXY_API = "http://47.244.189.91/delete-proxy"

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

# # ==================《mysql操作接口》====================
# DB_API_HOST = 'http://60.195.249.95:5001'
#
#
# # mysql数据增加接口
# DB_INSERT = '{}/mysql-insertData'.format(DB_API_HOST)
# # mysql数据删除接口
# DB_DELETE = '{}/mysql-deleteData'.format(DB_API_HOST)
# # mysql数据更新接口
# DB_UPDATE = '{}/mysql-updateData'.format(DB_API_HOST)
# # mysql表查询接口
# DB_SELECT = '{}/mysql-selectData'.format(DB_API_HOST)
# # 执行一条sql语句
# DB_EXECUTE = '{}/mysql-execute'.format(DB_API_HOST)
# # 任务插入接口
# DB_INSERT_TASK = '{}/mysql-insertTask'.format(DB_API_HOST)


# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'
