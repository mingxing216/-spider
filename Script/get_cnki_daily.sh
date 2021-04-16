#!/bin/bash

if [ -z $1 ]
then
  DATE=`date +%Y-%m-%d`
else
  DATE=$1
fi
echo $DATE
date

echo -n '成功任务次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task success' | wc -l

echo -n '失败任务次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task failed' | wc -l

echo -n '图片存储成功次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储附件成功' | wc -l

echo -n '实体存储成功次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储实体成功' | wc -l
