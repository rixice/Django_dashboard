#!/bin/bash

file=$1
size=`ls -lh $file| cut -d ' ' -f5`
echo $size
