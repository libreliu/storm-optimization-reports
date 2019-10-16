#!/bin/bash

dump_proc_img() {
	while true; do
		echo "Saving $1 & $2 on `date`..."
		echo "ps aux" | ssh $1 > ${1}_`date +%Y%m%d-%H%M%S`.txt
		echo "ps aux" | ssh $2 > ${2}_`date +%Y%m%d-%H%M%S`.txt
		sleep 15
	done
}


start_graph500() {
	./tcp.sh
}

if [ $# -ne 2 ]; then
	echo "Usage: $0 first_node second_node"
	exit
fi

read -p "Enter Test Case No. :" TESTCASE_NO
mkdir $TESTCASE_NO
cd $TESTCASE_NO

dump_proc_img $1 $2
