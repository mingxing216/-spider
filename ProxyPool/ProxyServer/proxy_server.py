# -*- coding:utf-8 -*-

# from gevent import monkey
# from gevent.pywsgi import WSGIServer
# monkey.patch_all()

from flask import Flask, request
from ProxyPool.Common.db import RedisClient
from ProxyPool.setting import *

__all__ = ['app']

app = Flask(__name__)

# app.debug = True
app.redis = None

def get_conn():
    if not app.redis:
        app.redis = RedisClient()
    return app.redis


@app.route('/')
def index():
    return '<h2>Welcome to Proxy Pool System</h2>'


@app.route('/proxy/add')
def add_proxy():
    """
    set max number proxy
    :param: ip
    :param: protocol
    :param: remain_time
    :return:
    """
    ip = request.args.get('ip')
    protocol = request.args.get('p')
    remain_time = request.args.get('rt')
    conn = get_conn()
    return str(conn.max(ip))


@app.route('/proxy/get')
def get_proxy():
    """
    Get a proxy
    :param: ws: website; 多网站管理
#   :param: protocol: http/socks5；协议，流媒体等；
#   :param: using_time: 3/5/30s；剩余时间管理；
    :return: 随机代理
    """
    ws = request.args.get('ws')
    protocol = request.args.get('p')
    using_time = request.args.get('ut')
    conn = get_conn()
    ip = conn.random()
    if ip:
        conn.modify_score(ip, -1)
        return ip
    else:
        return ''


@app.route('/proxy/release')
def release_proxy():
    """
    release proxy
    :param: ip
    :param: result: 代理成功true/代理失败false
    :return: 修改后的分数
    """
    ip = request.args.get('ip')
    result = request.args.get('result')
    conn = get_conn()
    if result == 'True':
        return str(conn.modify_score(ip, 1))
    else:
        return str(conn.modify_score(ip, ERROR_DELTA_SCORE))


@app.route('/proxypool/count')
def get_counts():
    """
    Get the count of proxies
    :return: 代理池总量
    """
    conn = get_conn()
    return str(conn.count())


@app.route('/proxypool/all')
def get_proxies():
    """
    Get all proxies
    :return: 代理池全部代理
    """
    conn = get_conn()
    return str(conn.all())


if __name__ == '__main__':
    app.run(API_HOST, API_PORT, threaded=True)
    # http_server = WSGIServer((API_HOST, API_PORT), app)
    # http_server.serve_forever()
