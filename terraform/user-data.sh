#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip -y
cd /opt/
while [[ ! -d gunslinger ]]
do
	:
done
cd gunslinger
while [[ ! -d gunslinger_rules ]]
do
	:
done
while [[ -z $(ls -A gunslinger_rules) ]]
do
	:
done
sudo pip3 install -r requirements.txt
sudo chmod +x launch.sh
echo "Running ./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${urlscan_query}${cron}${sqs_url}-d gunslinger_rules"
./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${urlscan_query}${cron}${sqs_url}-d gunslinger_rules
