# -*- coding: UTF-8 -*-
import re
import os

# 查询指定路径文件夹下都有哪些指定后缀文件
def getCsvFileList(path, postfix):
    file_name_list = []
    for file in os.listdir(path):
        try:
            file_name = re.findall(r"(.*?)\.{}".format(postfix), file)[0]
        except:
            pass
        else:
            file_name_list.append(file_name)

    return file_name_list

# 判断指定路径文件夹下是否包含某文件夹
def hasDir(path):
    if os.path.isdir(path):

        # 有， 返回True
        return True
    else:

        # 没有， 返回False
        return False

# 判断指定路径文件夹下是否包含某文件夹， 包含删除， 不包含创建
def selectDelAndCreateDir(path):
    has = hasDir(path)
    if has is True:
        # 删除文件夹下的所有文件
        files = getDirFiles(path)
        for file in files:
            os.remove(file)
        # 删除文件夹
        os.rmdir(path)
        # 创建文件夹
        os.mkdir(path)
    else:
        # 创建文件夹
        os.mkdir(path)

# 删除指定文件夹下所有文件
def delDir(path):
    # 删除文件夹下的所有文件
    files = getDirFiles(path)
    for file in files:
        os.remove(file)


# 查询指定路径文件夹下都有哪些文件
def getDirFiles(path):
    file_name_list = []
    for file in os.listdir(path):
        file_name_list.append(file)

    return file_name_list

# 创建文件夹
def createDir(path):
    os.mkdir(path)


# 根据文件名删除文件
def deleteFile(path):
    os.remove(path=path)
