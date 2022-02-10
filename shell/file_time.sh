#!/bin/bash

echo -n `ls -l $1/$2| awk '{print$6"-"$7"  "$8}' &`
