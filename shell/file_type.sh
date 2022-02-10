#!/bin/bash

file=$1
file_type=`file $file| awk '{print$2}' &`
echo -n $file_type
