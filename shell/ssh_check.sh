#!/bin/bash
echo $1 >> /etc/ansible/hosts
ansible $1 -m copy -a "src=/root/shell dest=/root" > /tmp/result
sed -i /$1/d /etc/ansible/hosts
