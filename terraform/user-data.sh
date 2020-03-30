#!/bin/bash

sudo apt install python3-pip
cd /opt/
git clone "https://github.com/JacobPimental/gunslinger.git"
cd gunslinger/gunslinger
./launch.sh ${slack_token}${urlscan_api_key}${num_workers}${queue_channel}${rule_dir}${urlscan_query}${num_results}${sqs_url}
