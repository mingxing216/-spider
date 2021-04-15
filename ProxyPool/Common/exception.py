#-*-coding:utf-8-*-

class PoolEmptyException(Exception):
    def __str__(self):
        return repr('代理池已经枯竭')
