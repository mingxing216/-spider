#!/bin/bash
# 统计单位时间内爬虫每个动作耗时（总动作耗时、总次数、平均耗时）
# Sample
# stat_action_time.sh ${date_str} 15:10:
date_str=$1
time_str=$2
echo "Date $date_str"
echo "Time $time_str"

echo -n "任务耗时 "
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'task end' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n '下载耗时 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'downloader end' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'hbase存储耗时 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'storage end' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'mysql存储耗时 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'mysql end' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'proxy代理耗时 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'proxy |' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'kns.cnki.net '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'downloader' | grep 'kns.cnki.net' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'chn.oversea.cnki.net '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'downloader' | grep 'chn.oversea.cnki.net' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n 'image.cnki.net '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'downloader' | grep 'image.cnki.net' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n '语种识别 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'service | 语种识别' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'

echo -n '获取任务 '
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${date_str}*.log | grep 'task | 获取 1 条任务' | grep " ${time_str}" | awk -F'|' '{print $3}' | awk -F' ' '{time+=$3;count+=1}END{print time, count, time/count}'
