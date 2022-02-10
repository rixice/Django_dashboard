#!/bin/bash

echo -e "`kubectl get deployments.apps -n $1 | awk 'NR>1{print $1}'| wc -l`\c"
