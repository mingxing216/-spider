#!/bin/sh
ps -ef|grep -v grep|grep proxy_set_meal_pool_main.py|while read u p o
do
    kill -9 $p
done

while true
do

    ps -fe|grep proxy_set_meal_pool_main.py |grep -v grep
    if [ $? -ne 0 ]
    then
        echo 'start process'
        nohup python3 main/proxy_set_meal_pool_main.py &
    else
        echo "runing....."

        sleep 1
    fi
done
#####