#-*-coding:utf-8-*-
# ----------------------------
# 公共配置
# ----------------------------

PROXY_TYPE='http' # 代理IP协议种类

MYSQL_POOL_MAX_NUMBER = 5 # Mysql最大连接池数量
REDIS_POOL_MAX_NUMBER = 50 # Redis最大连接池数量

REDIS_MAX = 10000 # 队列任务最大数
REDIS_MIN = 2000 # 队列内容最小数

CONCURRENT = 50 # 并发量

TIMEOUT=10 # 请求超时

# ----------------------------
# mysql表名配置/redis表配置
# ----------------------------

MYSQL_PAPER = 'job_paper' # 论文任务表

REDIS_XUEWEI_PAPER = 'zhiwang_xuewei_paper' # 学位论文_论文队列名
REDIS_XUEWEI_PAPER_LOCK = 'zhiwang_xuewei_paper_lock' # 学位论文_论文队列分布式锁名

REDIS_HUIYI_PAPER = 'zhiwang_huiyi_paper' # 会议论文_论文队列名
REDIS_HUIYI_PAPER_LOCK = 'zhiwang_huiyi_paper_lock' # 会议论文_论文队列分布式锁名

REDIS_QIKAN_PAPER = 'zhiwang_qikan_paper' # 期刊论文_论文队列名
REDIS_QIKAN_PAPER_LOCK = 'zhiwang_qikan_paper_lock' # 期刊论文_论文队列分布式锁名


MYSQL_MAGAZINE = 'job_magazine' # 期刊任务表

REDIS_HUIYI_MAGAZINE = 'zhiwang_huiyi_magazine' # 会议论文_期刊队列名
REDIS_HUIYI_MAGAZINE_LOCK = 'zhiwang_huiyi_magazine_lock' # 会议论文_期刊队列分布式锁名

REDIS_QIKAN_MAGAZINE = 'zhiwang_qikan_magazine' # 期刊论文_期刊队列名
REDIS_QIKAN_MAGAZINE_LOCK = 'zhiwang_qikan_magazine_lock' # 期刊论文_期刊队列分布式锁名


MYSQL_ACTIVITY = 'job_activity' # 活动任务表
REDIS_ZHIWANG_ACTIVITY = 'zhiwang_huiyi_activity' # 会议论文_活动队列名
REDIS_ZHIWANG_ACTIVITY_LOCK = 'zhiwang_huiyi_activity_lock' # 会议论文_活动队列分布式锁名


MYSQL_PEOPLE = 'job_people' # 作者任务表
REDIS_ZHIWANG_PEOPLE = 'zhiwang_people' # 论文_作者队列名
REDIS_ZHIWANG_PEOPLE_LOCK = 'zhiwang_people_lock' # 论文_作者队列分布式锁名


MYSQL_INSTITUTE = 'job_institute' # 机构任务表

REDIS_XUEWEI_INSTITUTE  = 'zhiwang_xuewei_institute' # 学位论文_学位授予单位队列名
REDIS_XUEWEI_INSTITUTE_LOCK = 'zhiwang_xuewei_institute_lock' # 学位论文_学位授予单位队列分布式锁名

REDIS_ZHIWANG_INSTITUTE  = 'zhiwang_institute' # 论文_机构队列名
REDIS_ZHIWANG_INSTITUTE_LOCK = 'zhiwang_institute_lock' # 论文_机构队列分布式锁名


MYSQL_IMG = 'job_img' # 图片任务表
REDIS_ZHIWNAG_IMG  = 'zhiwang_img' # 图片队列名
REDIS_ZHIWNAG_IMG_LOCK = 'zhiwang_img_lock' # 图片队列分布式锁名


# ----------------------------
# redis分类队列配置
# ----------------------------
REDIS_XUEWEI_CATEGORY = 'zhiwang_xuewei_category' # 学位论文分类队列
REDIS_XUEWEI_CATEGORY_LOCK = 'zhiwang_xuewei_category_lock' # 学位论文分类队列锁

REDIS_HUIYI_CATEGORY = 'zhiwang_huiyi_category' # 会议论文分类队列
REDIS_HUIYI_CATEGORY_LOCK = 'zhiwang_huiyi_category_lock' # 会议论文分类队列锁

REDIS_QIKAN_CATEGORY = 'zhiwang_qikan_category' # 期刊论文分类队列
REDIS_QIKAN_CATEGORY_LOCK = 'zhiwang_qikan_category_lock' # 期刊论文分类队列锁


REDIS_XUEWEI_CLASS = 'zhiwang_xuewei_class' # 学位论文二级分类队列
REDIS_XUEWEI_CLASS_LOCK = 'zhiwang_xuewei_class_lock' # 学位论文二级分类队列锁

REDIS_HUIYI_CLASS = 'zhiwang_huiyi_class' # 会议论文二级分类队列
REDIS_HUIYI_CLASS_LOCK = 'zhiwang_huiyi_class_lock' # 会议论文二级分类队列锁

REDIS_QIKAN_CLASS = 'zhiwang_qikan_class' # 期刊论文二级分类队列
REDIS_QIKAN_CLASS_LOCK = 'zhiwang_qikan_class_lock' # 期刊论文二级分类队列锁


REDIS_XUEWEI_CATALOG = 'zhiwang_xuewei_catalog' # 学位论文列表队列
REDIS_XUEWEI_CATALOG_LOCK = 'zhiwang_xuewei_catalog_lock' # 学位论文列表队列锁

REDIS_HUIYI_CATALOG = 'zhiwang_huiyi_catalog' # 会议论文列表队列
REDIS_HUIYI_CATALOG_LOCK = 'zhiwang_huiyi_catalog_lock' # 会议论文列表队列锁

REDIS_QIKAN_CATALOG = 'zhiwang_qikan_catalog' # 期刊论文列表队列
REDIS_QIKAN_CATALOG_LOCK = 'zhiwang_qikan_catalog_lock' # 期刊论文列表队列锁

