#!/bin/bash
kubectl get nodes >/dev/null 2>&1
echo $?
