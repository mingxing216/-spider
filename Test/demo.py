#-*-coding:utf-8-*-

from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import time

task_list = [i for i in range(1000)]
print(task_list)

def A(url) :
    print(url)
    time.sleep(10)


def process_1():
    threadpool = ThreadPool()

    for url in task_list:
        threadpool.apply_async(func=A, args=(url,))

    threadpool.close()
    threadpool.join()

po = Pool(8)
for i in range(8):
    po.apply_async(func=process_1)

po.close()
po.join()

