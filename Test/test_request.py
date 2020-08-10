# -*- coding:utf-8 -*-
import re
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import requests

from Utils import user_agent_u




def get_resp(url):
    print('请求url: {}'.format(url))
    headers = {
        'User-Agent': user_agent_u.get_ua(),
        'cookie': 'UM_distinctid=1725404ab3d386-0a7cbcacff1eb9-1b386256-13c680-1725404ab3e401; wdcid=6a8ae96755d6ff1e; ASP.NET_SessionId=wqpcpxwwj0te2l4lhlftqaq3; Hm_lvt_e5019afb8f1df701fe12ca6988a487e5=1594814436,1594814540,1595213832,1595921988; skybug=46c629a8306c41bd731afe1b03760367; CNZZDATA5545901=cnzz_eid%3D6527406-1594800783-%26ntime%3D1596171419; CNZZDATA5943370=cnzz_eid%3D1686962856-1594802077-%26ntime%3D1596170816; wdses=7edd4d28f931d416; UserViewPaperHistoryCookie=ViewHistoryList=&ViewHistoryList=7101780397; Hm_lpvt_e5019afb8f1df701fe12ca6988a487e5=1596175546; wdlast=1596175546; usercssn=UserID=358042&allcheck=F17C0FFB8394961B4A2CE0CA5760D699'
    }
    resp = requests.get(url=url, headers=headers)
    name = re.findall(r"\d+$", url)[0]
    with open(name + '.pdf', 'wb') as f:
        f.write(resp.content)

def run():
    # 待处理url
    url_list = [
        'http://www.nssd.org/articles/article_down.aspx?id=674209922',
        'http://www.nssd.org/articles/article_down.aspx?id=7101898504',
        'http://www.nssd.org/articles/article_down.aspx?id=7101898518',
        'http://www.nssd.org/articles/article_down.aspx?id=7101005945'
    ]

    # 创建线程池
    threadpool = ThreadPool(processes=4)
    for url in url_list:
        threadpool.apply_async(func=get_resp, args=(url,))

    threadpool.close()
    threadpool.join()

run()


# # 创建进程池
# pool = Pool(processes=2)
# for i in range(2):
#     pool.apply_async(func=run)
#
# pool.close()
# pool.join()