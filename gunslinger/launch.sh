URLSCAN_KEY=""
SLACK_TOKEN=""
QUEUE_CHANNEL="-c mq "
SQS_URL=""
RULE_DIR=""
QUERY=""
CRON=""
NUM_WORKERS=5

while [[ $# -gt 0 ]]
do
	case "$1" in
		-u|--urlscan_key)
			URLSCAN_KEY="-u $2 "
			shift
			shift
			;;

		-s|--slack_token)
			SLACK_TOKEN="-s $2 "
			shift
			shift
			;;

		-c|--queue_channel)
			QUEUE_CHANNEL="-c $2 "
			shift
			shift
			;;

		-a|--sqs_url)
			SQS_URL="-a $2 "
			shift
			shift
			;;

		-d|--rule_dir)
			RULE_DIR="-d $2 "
			shift
			shift
			;;

		-q|--query)
			QUERY="-q $2 "
			shift
			shift
			;;

		-cr|--cron)
			CRON="-cr $2 "
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
if [ -z "$SQS_URL" ]
then
	reload_cmd="python3 reloader.py $URLSCAN_KEY$SLACK_TOKEN$QUEUE_CHANNEL$QUERY$CRON-w $NUM_WORKERS"
else
	reload_cmd="python3 reloader.py $URLSCAN_KEY$SQS_URL$QUEUE_CHANNEL$QUERY$CRON-w $NUM_WORKERS"
fi

gunslinger_cmd="python3 gunslinger.py $URLSCAN_KEY$SLACK_TOKEN$SQS_URL$QUEUE_CHANNEL$RULE_DIR"
echo $reload_cmd
echo $gunslinger_cmd

mkdir logs
nohup $reload_cmd 1>logs/reloader.log 2>logs/reloader\_err.log &
for i in $(seq 1 $NUM_WORKERS)
do
	nohup $gunslinger_cmd 1>logs/worker$i.log 2>logs/worker$i\_err.log &
	if [ -z "$SQS_URL" ]
	then
		sleep 60
	fi
done

