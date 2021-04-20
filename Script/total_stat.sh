#!/bin/bash

DATE=$1
echo $DATE
cat /opt/Log/cnki/${DATE}.cnki | grep Total | awk -F' ' '{count[$1]+=$3}END{for (i in count) { print i, count[i] }}'| sort
