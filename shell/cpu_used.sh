#!/bin/bash

cpu_free=`top -b -n2| grep Cpu| awk 'NR==2{print$8}'`
cpu_total=100

echo "$cpu_total-$cpu_free"|bc
