# -*- coding: utf-8 -*-

"""
本文件负责提供关于时间操作的公共方法
需要对时间进行操作，直接导入本文件，对应调用功能函数即可。
部分函数需要传参
"""

import time
import datetime
import re


def get_now_date():
    """
    获取当前日期
    :return: 2018-10-04
    """

    return time.strftime('%Y-%m-%d')


def get_now_datetime():
    """
    获取当前日期 + 时间
    :return: 2018-10-04 10:38:03
    """

    return time.strftime('%Y-%m-%d %H:%M:%S')


def get_current_second():
    """
    获取当前时间戳（秒）
    :return: 1538621331
    """
    t = time.time()

    return int(round(t))


def second_to_datetime(timestamp, default_format="%Y-%m-%d %H:%M:%S"):
    """
    将时间戳变成日期 + 时间
    :param timestamp: 时间戳（秒）
    :param default_format: 输出时间格式
    :return: 2018-10-04 10:38:03
    """
    time_local = time.localtime(timestamp)
    dt = time.strftime(default_format, time_local)

    return dt


def get_before_dawn_second():
    """
    获取今日凌晨时间戳
    :return: 1538582400
    """
    today = datetime.date.today()

    return int(time.mktime(today.timetuple()))


def get_monday_date():
    """
    获取本周一日期
    :return: 2018-10-01
    """
    monday_stamp = (datetime.datetime.today() -
                    datetime.timedelta(days=time.localtime().tm_wday)
                    ).strftime("%Y-%m-%d")

    return monday_stamp


def get_before_monday_date():
    """
    获取上周，周一日期
    :return: 2018-09-24
    """
    before_monday_date = (datetime.datetime.today() -
                          datetime.timedelta(days=time.localtime().tm_wday + 1 + 6)
                          ).strftime("%Y-%m-%d")

    return before_monday_date


def get_before_sunday_date():
    """
    获取上周，周日日期
    :return: 2018-09-30
    """
    before_sunday_date = (datetime.datetime.today() -
                          datetime.timedelta(days=time.localtime().tm_wday + 1)
                          ).strftime("%Y-%m-%d")

    return before_sunday_date


def get_before_2_monday_date():
    """
    获取上上周，周一日期
    :return: 2018-09-17
    """
    before_monday_date = (datetime.datetime.today() -
                          datetime.timedelta(days=time.localtime().tm_wday + 2 + 12)
                          ).strftime("%Y-%m-%d")

    return before_monday_date


def get_before_2_sunday_date():
    """
    获取上上周，周日日期
    :return: 2018-09-30
    """
    before_sunday_date = (datetime.datetime.today() -
                          datetime.timedelta(days=time.localtime().tm_wday + 1 + 7)
                          ).strftime("%Y-%m-%d")

    return before_sunday_date


def get_before_week_now_second(time_data, n=1):
    """
    获取n周以前的当前时间戳
    :param time_data: 2018-10-04 11:05:03
    :param n: 周数
    :return: 1536807903
    """
    time_array = time.strptime(time_data, "%Y-%m-%d %H:%M:%S")
    the_time = int(time.mktime(time_array))
    timestamp = the_time - (int(n) * 604800)

    return timestamp


def second_to_week_number(time_stamp):
    """
    获取指定时间戳是周几
    :param time_stamp: 时间戳（秒）
    :return: 1-7
    """
    str_date = second_to_datetime(time_stamp)
    date = datetime.datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S")
    week_num = date.weekday()

    return week_num + 1


def str_date_to_second(str_date):
    """
    将字符串类型时间转换成时间戳
    :param str_date: 2018-10-04 11:12:52
    :return: 1538622772
    """
    time_array = time.strptime(str_date, "%Y-%m-%d %H:%M:%S")
    time_stamp = int(time.mktime(time_array))

    return time_stamp


def str_date_to_datetime(str_date):
    """
    将字符串类型时间 转换成 时间类型时间
    :param str_date: 2018-10-04 11:14:37（str）
    :return: 2018-10-04 11:14:37（datetime.datetime）
    """

    return datetime.datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S")


def get_stamp_from_monday(stamp, default_format="%Y-%m-%d %H:%M:%S"):
    """
    获取指定时间戳的周一日期
    :param stamp: 时间戳（秒）
    :param default_format: 输出时间格式
    :return: 2018-10-01 11:16:54
    """
    week_num = second_to_week_number(stamp)
    if week_num == 1:

        return second_to_datetime(stamp, default_format)
    else:

        return second_to_datetime(stamp - (86400 * (week_num - 1)), default_format)


def get_date_time_record(str_date):
    """
    将字符串类型时间 转换成 时间记录
    用于网页日期格式不统一的情况下 最少要有年
    :param str_date: '2019-5-21 10:21:35'
    :return: {'Y':2019, 'M':5, 'D':21, 'h':10, 'm':21, 's':35}
    """
    dateList = re.findall(
        r"([\d]{4})([-/年]([\d]{1,2}))?([-/月]([\d]{1,2})[日]?)?([\s]+([\d]{1,2})([:：时]([\d]{1,2})([:：分]([\d]{1,2})[秒]?)?)?)?",
        str_date)
    if dateList:
        res = {'Y': int(dateList[0][0])}
        if dateList[0][2]:
            res['M'] = (int(dateList[0][2]))
        if dateList[0][4]:
            res['D'] = (int(dateList[0][4]))
        if dateList[0][6]:
            res['h'] = (int(dateList[0][6]))
        if dateList[0][8]:
            res['m'] = (int(dateList[0][8]))
        if dateList[0][10]:
            res['s'] = (int(dateList[0][10]))
    else:
        res = ""
    return res


def get_date_time(str_date):
    """
    将字符串类型时间 转换成 标准格式时间
    用于网页日期格式统一的情况下 最少要有年
    :param str_date: '2019年5'
    :return: 2019-05-01 00:00:00
    """
    # dateList = re.findall(r'(?:([\d]{4})[-/年])?([\d]{1,2})[-/月]([\d]{1,2})[日]?([\s]+([\d]{1,2})([:时]([\d]{1,2})([:分]([\d]{1,2})[秒]?)?)?)?', str_date)
    dateList = re.findall(
        r"([\d]{4})([-/年]([\d]{1,2}))?([-/月]([\d]{1,2})[日]?)?([\s]+([\d]{1,2})([:：时]([\d]{1,2})([:：分]([\d]{1,2})[秒]?)?)?)?",
        str_date)
    if len(dateList) == 0 or len(dateList[0][0]) < 4:
        return ""
    # date = (int(dateList[0][0]) if dateList[0][0] else datetime.datetime.now().year, int(dateList[0][1]), int(dateList[0][2]), int(dateList[0][4]) if dateList[0][4] else 0, int(dateList[0][6]) if dateList[0][6] else 0, int(dateList[0][8]) if dateList[0][8] else 0, 0, 0, 0)
    date = (int(dateList[0][0]) if dateList[0][0] else datetime.datetime.now().year,
            int(dateList[0][2]) if dateList[0][2] else 0, int(dateList[0][4]) if dateList[0][4] else 0,
            int(dateList[0][6]) if dateList[0][6] else 0, int(dateList[0][8]) if dateList[0][8] else 0,
            int(dateList[0][10]) if dateList[0][10] else 0, 0, 0, 0)
    return time.strftime('%Y-%m-%d %H:%M:%S', date)
