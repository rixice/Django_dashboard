#!/bin/bash
ls -al ~/.ssh/id_*.pub >/dev/null
server_ip_address=$1
server_passwd=$2
apt -y install sshpass
if [[ $? -gt 0 ]];then
	ssh-keygen -f ~/.ssh/id_rsa -t rsa -N ''
	ping -c1 $server_ip_address > /dev/null
	if [[ $? -eq 0 ]];then
		expect <<EOF
		spawn ssh-copy-id $server_ip_address
		expect {
        		"*yes/no*" {send "yes\r" ; exp_continue}
        		"*password*" {send "$server_passwd\r" ; exp_continue}
    		}
EOF
	fi
else
	ping -c1 $server_ip_address >/dev/null
	if [[ $? -eq 0 ]];then  
                expect -c "set timeout -1;
    		spawn ssh-copy-id $server_ip_address;
    		expect {
        		*(yes/no)* {send -- yes\r;exp_continue;}
        		*assword:* {send -- $server_passwd\r;exp_continue;}
        		eof {exit 0;}
    		}";
	fi
fi
