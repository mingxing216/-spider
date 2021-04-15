# -*- coding:utf-8 -*-
import sys
import io

from Log import logging
from ProxyPool.scheduler import Scheduler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    try:
        s = Scheduler()
        s.run()
    except Exception as e:
        print("Run | exception {}".format(e))


if __name__ == '__main__':
    main()
