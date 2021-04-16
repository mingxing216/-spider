#!/bin/bash
for m in `cat crawler.hosts`;
do
  echo $m;
  ssh $m "sh /home/project/SpiderProject/SpiderFrame/Script/stat_action_time.sh $1 $2";
done
