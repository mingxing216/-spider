#!/bin/bash
for m in `cat crawler.hosts`;
do
  echo $m;
  ssh $m "sh /home/project/SpiderProject/SpiderFrame/Script/get_cnki.sh $1";
done
