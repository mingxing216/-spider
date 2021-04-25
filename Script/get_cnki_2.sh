#!/bin/bash

if [ -z $1 ]
then
  DATE=`date +%Y-%m-%d`
else
  DATE=$1
fi
echo $DATE
date

TEMP_FILE=/tmp/get_cnki_${DATE}.tmp

echo "Create Temp file ${TEMP_FILE}"
cat /opt/Log/ZhiWangLunWen/期刊论文_data_${DATE}*.log | grep -E '(task|storage|downloader) end' > $TEMP_FILE
echo "Temp file created"
ls -alh $TEMP_FILE

echo '总任务次数 时间分布'
cat $TEMP_FILE | grep 'task end' | awk -F':' '{print $1}' | sort | uniq -c| awk -F' ' '{print $0; total += $1} END {print "总任务次数 Total ", total;}'

echo '成功任务次数 时间分布'
cat $TEMP_FILE | grep 'task end' | grep 'task success' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "成功任务次数 Total ", total;}'

echo '失败任务次数 时间分布'
cat $TEMP_FILE | grep 'task end' | grep 'task failed' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "失败任务次数 Total ", total;}'

echo '总下载次数 时间分布'
cat $TEMP_FILE | grep 'downloader end' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "总下载次数 Total ", total;}'

echo  '下载成功次数 时间分布'
cat $TEMP_FILE | grep 'downloader end' | grep '下载成功' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "下载成功次数 Total ", total;}'

echo  '下载失败次数 时间分布'
cat $TEMP_FILE | grep 'downloader end' | grep '下载失败' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "下载失败次数 Total ", total;}'

echo '总存储次数 时间分布'
cat $TEMP_FILE | grep 'storage end' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "总存储次数 Total ", total;}'

echo '图片存储成功次数 时间分布'
cat $TEMP_FILE | grep 'storage end' | grep '存储附件成功' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "图片存储成功次数 Total ", total;}'

echo '图片存储失败次数 时间分布'
cat $TEMP_FILE | grep 'storage end' | grep '存储附件失败' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "图片存储失败次数 Total ", total;}'

echo '实体存储成功次数 时间分布';
cat $TEMP_FILE | grep 'storage end' | grep '存储实体成功' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "实体存储成功次数 Total ", total;}'

echo '实体存储失败次数 时间分布'
cat $TEMP_FILE | grep 'storage end' | grep '存储实体失败' | awk -F':' '{print $1}' | sort | uniq -c | awk -F' ' '{print $0; total += $1} END {print "实体存储失败次数 Total ", total;}'

rm $TEMP_FILE