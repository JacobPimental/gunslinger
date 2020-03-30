#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip -y
cd /opt/
git clone "https://github.com/JacobPimental/gunslinger.git"
cd gunslinger/gunslinger
sudo pip3 install -r requirements.txt
./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${rule_dir}${urlscan_query}${num_results}${sqs_url}
