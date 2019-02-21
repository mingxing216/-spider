#-*-coding:utf-8-*-


# 代理IP协议种类
PROXY_TYPE='http'

# 代理重复获取次数
UPDATE_PROXY_FREQUENCY=8

# 同IP重复请求次数
RETRY=5

# 请求超时
TIMEOUT=5

# 代理IP所属国家
COUNTRY=1

# 进程数
PROCESS_NUMBER=1

# mysql连接池数量
MYSQLPOOL_NUMBER = 1

# 栏目——抓取模板1
COLUMN_INDEX_1 = [
    {'时政': 'http://m.xinhuanet.com/politics/index.htm'},
    {'财经': 'http://m.xinhuanet.com/fortune/index.htm'},
    {'国际': 'http://m.xinhuanet.com/world/index.htm'},
    {'娱乐': 'http://m.xinhuanet.com/ent/index.htm'},
    {'图片': 'http://m.xinhuanet.com/photo/index.htm'},
    {'军事': 'http://m.xinhuanet.com/mil/index.htm'},
    {'体育': 'http://m.xinhuanet.com/sports/index.htm'},
    {'教育': 'http://m.xinhuanet.com/edu/index.htm'},
    {'网评': 'http://m.xinhuanet.com/comments/index.htm'},
    {'港澳台': 'http://m.xinhuanet.com/gangao/index.htm'},
    {'法治': 'http://m.xinhuanet.com/legal/index.htm'},
    {'社会': 'http://m.xinhuanet.com/society/index.htm'},
    {'文化': 'http://m.xinhuanet.com/culture/index.htm'},
    {'时尚': 'http://m.xinhuanet.com/fashion/index.htm'},
    {'旅游': 'http://m.xinhuanet.com/travel/index.htm'},
    {'健康': 'http://m.xinhuanet.com/health/index.htm'},
    {'汽车': 'http://m.xinhuanet.com/auto/index.htm'},
    {'房产': 'http://m.xinhuanet.com/house/index.htm'},
    {'美食': 'http://m.xinhuanet.com/food/index.htm'},
    {'悦读': 'http://m.xinhuanet.com/book/index.htm'},
    {'视频': 'http://m.xinhuanet.com/video/index.htm'},
    {'新华社新闻': 'http://m.xinhuanet.com/xhsxw/index.htm'},
    {'滚动新闻': 'http://m.xinhuanet.com/gdxw/index.htm'},
    {'北京': 'http://m.news.cn/bj.htm'},
    {'天津': 'http://m.news.cn/tj.htm'},
    {'河北': 'http://m.news.cn/he.htm'},
    {'山西': 'http://m.news.cn/sx.htm'},
    {'辽宁': 'http://m.news.cn/ln.htm'},
    {'吉林': 'http://m.news.cn/jl.htm'},
    {'上海': 'http://m.news.cn/sh.htm'},
    {'江苏': 'http://m.news.cn/js.htm'},
    {'浙江': 'http://m.news.cn/zj.htm'},
    {'安徽': 'http://m.news.cn/ah.htm'},
    {'福建': 'http://m.news.cn/fj.htm'},
    {'江西': 'http://m.news.cn/jx.htm'},
    {'山东': 'http://m.news.cn/sd.htm'},
    {'河南': 'http://m.news.cn/ha.htm'},
    {'湖北': 'http://m.news.cn/hb.htm'},
    {'湖南': 'http://m.news.cn/hn.htm'},
    {'广东': 'http://m.news.cn/gd.htm'},
    {'广西': 'http://m.news.cn/gx.htm'},
    {'海南': 'http://m.news.cn/hq.htm'},
    {'重庆': 'http://m.news.cn/cq.htm'},
    {'四川': 'http://m.news.cn/sc.htm'},
    {'贵州': 'http://m.news.cn/gz.htm'},
    {'云南': 'http://m.news.cn/yn.htm'},
    {'西藏': 'http://m.news.cn/xz.htm'},
    {'陕西': 'http://m.news.cn/sn.htm'},
    {'甘肃': 'http://m.news.cn/gs.htm'},
    {'青海': 'http://m.news.cn/qh.htm'},
    {'宁夏': 'http://m.news.cn/nx.htm'},
    {'新疆': 'http://m.news.cn/xj.htm'},
    {'内蒙古': 'http://m.news.cn/nmg.htm'},
    {'黑龙江': 'http://m.news.cn/hlj.htm'}
]