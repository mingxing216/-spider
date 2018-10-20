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

# redis
REDIS_HOST='127.0.0.1'
REDIS_PORT=6379
REDIS_PASSWORD='rockerfm520'

# MongoDB
M_HOST='127.0.0.1'
M_PORT=27017


# 线上芝麻代理套餐==========================================

ZHIMA_SETMEAL=32716 # 芝麻代理套餐号
REDIS_PROXY_KEY='zhimaProxyPool' # redis中保存代理IP的列表名
REDIS_PROXY_NUMBER=2 # redis中保存代理IP的数量

# 芝麻套餐余量查询参数
SETMEALNEEK=54871
SETMEALAPPKEY='fd2f243b621fd4fef564c5a80a6c1a65'
AC=ZHIMA_SETMEAL

# =======================================================

# 知网期刊爬虫最大进程数
ZHIWANG_PERIODOCAL_SPIDER_PROCESS = 4




# # oss
# ACCESSKEYID='LTAITx7i8MVIqSWh'
# ACCESSKEYSECRET='kwXFGPMeO4JtsTXs7Pa4zeJZhvsbaK'
# ENDPOINT='http://oss-us-west-1.aliyuncs.com'
# BUCKET='candylake-vd'
# # oss文件上传域名
# UPLOADPATH='http://vt.candlake.com'
