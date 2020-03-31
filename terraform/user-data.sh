#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip -y
cd /opt/
while [[ ! -d gunslinger_rules ]]
do
	:
done
git clone "https://github.com/JacobPimental/gunslinger.git"
mv gunslinger_rules gunslinger/gunslinger/
cd gunslinger/gunslinger
sudo pip3 install -r requirements.txt
echo "Running ./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${urlscan_query}${num_results}${sqs_url}-d gunslinger_rules"
./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${urlscan_query}${num_results}${sqs_url}-d gunslinger_rules
