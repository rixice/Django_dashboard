#!/bin/bash

ip=$(ifconfig 'ens33'| grep inet| awk 'NR==1{print$2}'| cut -d ":" -f 2)

echo -n $ip
