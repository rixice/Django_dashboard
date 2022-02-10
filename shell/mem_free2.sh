#!/bin/bash

mem_free=`top -b -n1| awk 'NR==4{print$6}'`
mem_total=`top -b -n1| awk 'NR==4{print$4}'`

echo "$mem_total-$mem_free"|bc
