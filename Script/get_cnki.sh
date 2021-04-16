#!/bin/bash

if [ -z $1 ]
then
  DATE=`date +%Y-%m-%d`
else
  DATE=$1
fi
echo $DATE
date

echo '总任务次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '总任务次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | wc -l

echo '成功任务次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task success' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '成功任务次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task success' | wc -l

echo '失败任务次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task failed' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '失败任务次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'task end' | grep 'task failed' | wc -l

echo '总下载次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '总下载次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | wc -l

echo  '下载成功次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | grep '下载成功' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '下载成功次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | grep '下载成功' | wc -l

echo  '下载失败次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | grep '下载失败' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '下载失败次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'downloader end' | grep '下载失败' | wc -l

echo '总存储次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '总存储次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | wc -l

echo '图片存储成功次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储附件成功' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '图片存储成功次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储附件成功' | wc -l

echo '图片存储失败次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储附件失败' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '图片存储失败次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储附件失败' | wc -l

echo '实体存储成功次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储实体成功' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '实体存储成功次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储实体成功' | wc -l

echo '实体存储失败次数 时间分布'
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储实体失败' | awk -F':' '{print $1}' | sort | uniq -c
echo -n '实体存储失败次数 Total '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep 'storage end' | grep '存储实体失败' | wc -l
