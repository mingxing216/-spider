#-*-coding:utf-8-*-

'''
测试环境配置参数
'''

# Mysql
DB_HOST='60.195.249.104'
DB_PORT=3306
DB_USER='spider'
DB_PASS='spider'
DB_NAME='spider'

# redis
REDIS_HOST='127.0.0.1'
REDIS_PORT=6379
REDIS_PASSWORD='spider'

# MongoDB
M_HOST='127.0.0.1'
M_PORT=27017

# 芝麻账号余额接口参数
NEEK=53686
APPKEY='c19deb9221b9091d61bc4d4d8d2cc3ab'

ZHIMA_SETMEAL=31557 # 芝麻代理套餐号
REDIS_PROXY_KEY='proxy' # redis中保存代理IP的列表名
REDIS_PROXY_NUMBER=20 # redis中保存代理IP的数量

# 芝麻套餐余量查询参数
SETMEALNEEK=53686
SETMEALAPPKEY='3c198ca8d4e37e8f1507e8e136205a77'
AC=ZHIMA_SETMEAL

# 知网期刊爬虫最大线程数
ZHIWANG_PERIODOCAL_SPIDER_THREAD = 10
# 知网期刊爬虫最大进程数
ZHIWANG_PERIODOCAL_SPIDER_PROCESS = 4


# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'