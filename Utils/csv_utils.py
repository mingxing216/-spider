# -*- coding: UTF-8 -*-
import csv


def create_csv_file(csv_name, csv_title_list):
    """
    创建csv文件
    :param csv_name: 文件路径/文件名.csv
    :param csv_title_list: 字段列表
    """
    out = open(csv_name, 'a', encoding='utf-8-sig')
    csv_write = csv.writer(out, dialect='excel')
    csv_write.writerow(csv_title_list)


def read_csv_file(csv_path):
    """
    读取csv文件内容
    :param csv_path: 文件路径/文件名.csv
    """
    with open(csv_path) as f:
        reader = csv.reader(f)

        # reader是列表类型数据， 元素也是列表
        return list(reader)


# 追加数据
def append_data(csv_name, data_list):
    """
    追加数据
    :param csv_name: 文件路径/文件名.csv
    :param data_list: 内容列表
    """
    out = open(csv_name, 'a', encoding='utf-8-sig')
    csv_write = csv.writer(out, dialect='excel')
    csv_write.writerow(data_list)
