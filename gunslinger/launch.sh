NUM_WORKERS=5
CONFIG_FILE="-c gunslinger.yaml"

while [[ $# -gt 0 ]]
do
	case "$1" in
		-c|--config-file)
			QUEUE_CHANNEL="-c $2 "
			shift
			shift
			;;

		-t|--num_workers)
			NUM_WORKERS="$2"
			shift
			shift
			;;
	esac
done

mkdir logs

chmod +x inputs/*

for f in inputs/*
do
	cmd="./$f $CONFIG_FILE"
	bn=$(basename $f)
	nohup $cmd &
done
sleep 60
gunslinger_cmd="python3 gunslinger.py $CONFIG_FILE"
echo $gunslinger_cmd
for i in $(seq 1 $NUM_WORKERS)
do
	nohup $gunslinger_cmd &
	if [ -z "$SQS_URL" ]
	then
		sleep 60
	fi
done

