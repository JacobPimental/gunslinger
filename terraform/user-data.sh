#!/bin/bash
sudo apt update
sudo apt upgrade --yes --force-yes -o Dpkg::Options::="--force-confnew"
sudo apt install python3-pip --yes --force-yes
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
echo "Running ./launch.sh ${num_workers}"
./launch.sh ${num_workers}
