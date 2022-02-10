#!/bin/bash

top_cpu=$(top -b -n1|awk 'NR==8{print$9}')
echo $top_cpu
