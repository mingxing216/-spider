#-*-coding:utf-8-*-


# 代理IP协议种类
PROXY_TYPE = 'http'

# 代理重复获取次数
UPDATE_PROXY_FREQUENCY = 8

# 同IP重复请求次数
RETRY = 5

# 请求超时
TIMEOUT = 5

# 代理IP所属国家
COUNTRY = 1

# mysql存储url表名
MYSQL_URL_TABLE = 'ss_zhiwang_zhuanli_url'

# redis队列url集合名
REDIS_URL_TABLE = 'ss_zhiwang_zhuanli_url'

# 每次从redis获取任务的数量
REDIS_GET_NUMBER = 100

# 进程数
PROCESS_NUMBER = 8