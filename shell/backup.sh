#!/bin/bash

nohup tar cpzf $1 --exclude=$2 --exclude=$3 --exclude=$4 --exclude=$5 --exclude=$6 / &
