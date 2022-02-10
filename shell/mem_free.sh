#!/bin/bash

mem_free=`top -n1| awk 'NR==4{print$6}'`
mem_total=`top -n1| awk 'NR==4{print$4}'`

mem_u=`echo "$mem_total-$mem_free"|bc`
echo "scale=2;$mem_u/$mem_total"|bc |cut -d "." -f 2-3


