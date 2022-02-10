#!/bin/bash

echo "`kubectl get deployment -n $1| awk 'NR>1{print$5}'`"

