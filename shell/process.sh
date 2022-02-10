#!/bin/bash

process_top=$(top -b -n1| awk 'NR==8{print$12}')

echo $process_top
