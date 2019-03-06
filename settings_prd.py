#-*-coding:utf-8-*-

'''
线上环境配置参数
'''

# Mysql
DB_HOST='60.195.249.105'
DB_PORT=3306
DB_USER='spider'
DB_PASS='spider'
DB_NAME='spider'
DB_POOL_NUMBER=10 # 连接池内连接默认数量

# redis
REDIS_HOST='60.195.249.105'
REDIS_PORT=6379
REDIS_PASSWORD='spider'
REDIS_POOL_MAX_NUMBER=10 # redis链接池最大连接数

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
SpiderDataSaveUrl='http://60.195.249.117:8090/hbaseserver/dat/saveStructuredData?'
# hbase存储爬虫输出多媒体文件
SpiderMediaSaveUrl='http://60.195.249.117:8090/hbaseserver/dat/saveMediaData?'

# ==================《adsl代理池》==================

# 获取代理接口
GET_PROXY_API = "http://60.195.249.95:5000/get-proxy"
# 代理状态更新接口
UPDATE_PROXY_API = "http://60.195.249.95:5000/update-proxy"
# 删除代理接口
DELETE_PROXY_API = "http://60.195.249.95:5000/delete-proxy"

# mysql数据库存储流媒体文件url的表名
MEDIA_TABLE = 'ss_media'
# mysql数据库记录已存数据的表名
STATISTICS_TABLE = 'ss_statistics'

# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'