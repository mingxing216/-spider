# -*- coding:utf-8 -*-

# Redis数据库地址
REDIS_HOST = '192.168.10.93'

# Redis端口
REDIS_PORT = 6379

# Redis密码，如无填None
REDIS_PASSWORD = 'onecooo'

REDIS_KEY = 'proxies'

REDIS_POOL_MAX_NUMBER = 50

# 代理分数
INITIAL_SCORE = 300
MAX_SCORE = 300
MIN_SCORE = 0
ERROR_DELTA_SCORE = -50

# 一次获取代理数量
PROXIES_NUM = 1

# 删除区间
DELETE_MIN = 0
DELETE_MAX = 20

VALID_STATUS_CODES = [200, 302]

# 代理池数量界限
POOL_UPPER_THRESHOLD = 10000

# 代理允许池最大数量
POOL_MAX_COUNT = 100

# 检查周期
TESTER_CYCLE = 5
# 获取周期
GETTER_CYCLE = 20

# 测试API，建议抓哪个网站测哪个
TEST_URL = 'https://www.baidu.com/'

# API配置
API_HOST = '0.0.0.0'
API_PORT = 5000

# 开关
TESTER_ENABLED = False
GETTER_ENABLED = True
API_ENABLED = True

# 最大批测试量
BATCH_TEST_SIZE = 10
