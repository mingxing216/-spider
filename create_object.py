#-*-coding:utf-8-*-
import sys
import os


def alter(file,old_str,new_str):
    """
    替换文件中的字符串
    :param file:文件名
    :param old_str:就字符串
    :param new_str:新字符串
    :return:
    """
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str,new_str)
            file_data += line
    with open(file,"w",encoding="utf-8") as f:
        f.write(file_data)

if __name__ == '__main__':
    object_name = sys.argv[1]
    os.system('cp -r Project_Template/ProjectTemplate Test/{}'.format(object_name))
    alter('Test/{}/main/main.py'.format(object_name), "Project_Template", "Test")
    alter('Test/{}/main/main.py'.format(object_name), "ProjectTemplate", "{}".format(object_name))
    alter('Test/{}/main/main.py'.format(object_name), "log_file_dir = ''", "log_file_dir = '{}'".format(object_name))










