![](docs/images/logo.png)
# Gunslinger 
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/S6S89H72)<br>
"The man in black fled across the desert, and the gunslinger followed."<br>
\- Stephen King, The Gunslinger<br><br>
Gunslinger is a hunting tool that is based around URLScan's Search API. Gunslinger can crawl URLScan for JavaScript files that match a set of user-defined rules and reports the information back to Slack.

## Usage
Gunslinger can be deployed via the Terraform modules in the `terraform` directory. If you have Terraform installed you can deploy the script by running `terraform apply` while in the directory.
### Terraform Variables
```
#Digital Ocean Variables
digitalocean_token: Used to deploy the Gunslinger server to DigitalOcean
server_pub_key: Path to the public SSH key for the server
server_priv_key: Path to the private SSH key for the server (Used to scp scripts once deployed)
server_region: DigitalOcean region to deploy the server to (default: nyc1)

#API Keys
slack_token: API Key for the Slack Bot that will be used
urlscan_api_key: API Key to connect to URLScan

#Launch Script Variables
rule_dir: Path to directory where custom rules are stored (default: "../gunslinger/rules")
num_workers: Number of gunslinger workers to spin up (default: 5)
queue_channel: Slack Channel to use as a Message Queue (default: mq)
urlscan_query: Query to use for URLScan Search API (default: *)
cron: Cron schedule for the reloader module (note: replace asterisks with underscores; default: _ _ _ _ _ (every minute))

#Miscellaneous
aws_region: Region to deploy any AWS resources (default: us-east-1)
use_sqs: Whether or not to use AWS SQS for the Message Queue (default: false)
```

## Python Modules
### Reloader Module
This module will reach out to URLScan's search API on a specified cron schedule, split up the results between the number of gunslinger worker, and post that info the the Message Queue.
#### Usage:
```
usage: reloader.py [-h] -u URLSCAN_KEY [-s SLACK_TOKEN] [-c QUEUE_CHANNEL] [-q QUERY] [-cr CRON CRON CRON CRON CRON] [-w NUM_WORKERS] [-a SQS_URL]

optional arguments:
  -h, --help            show this help message and exit
  -u URLSCAN_KEY, --urlscan_key URLSCAN_KEY
                        URLScan API key
  -s SLACK_TOKEN, --slack_token SLACK_TOKEN
                        Slack Token
  -c QUEUE_CHANNEL, --queue_channel QUEUE_CHANNEL
                        Message Queue Channel (Default: 5)
  -q QUERY, --query QUERY
                        URLScan query (Default: *)
  -cr CRON CRON CRON CRON CRON, --cron CRON CRON CRON CRON CRON
                        Cron job for searches to run on (Default: _ _ _ _ _)
  -w NUM_WORKERS, --num_workers NUM_WORKERS
                        Number of gunslinger works to divy tasks(Default: 5)
  -a SQS_URL, --sqs_url SQS_URL
                        AWS SQS Url (optional)
```
### Gunslinger Module
This is the main worker module that will analyze jobs from the Reloader module and post results back to Slack. It is driven by a set of user-defined rules to perform its analysis.
#### Usage:
```
usage: gunslinger.py [-h] -u URLSCAN_KEY -s SLACK_TOKEN [-c QUEUE_CHANNEL] [-d RULE_DIR] [-a SQS_URL]

optional arguments:
  -h, --help            show this help message and exit
  -u URLSCAN_KEY, --urlscan_key URLSCAN_KEY
                        URLScan API key
  -s SLACK_TOKEN, --slack_token SLACK_TOKEN
                        Slack Token
  -c QUEUE_CHANNEL, --queue_channel QUEUE_CHANNEL
                        Message Queue Channel (Default: mq)
  -d RULE_DIR, --rule_dir RULE_DIR
                        Directory containing python plugins to be used as rules (Default: ./rules)
  -a SQS_URL, --sqs_url SQS_URL
                        URL of AWS SQS service (optional)
```

## Rule Creation
Gunslinger is driven y a set of user-defined Python modules that act as rules. This way the user has free reign over how to handle information. All modules must be contained in one directory (`rules` by default) and must have a function named `run` that will be called when analyzing scripts. The arguments passed to this function will be a string called `script` containing the script that was found by URLScan's API and a JSON object called `response_data` which contains the data returned from URLScan's API (see URLScan's API [documentation](https://urlscan.io/about-api/) for more info).
### Example:
This is a very basic example that will catch an older Magecart sample from e4[.]ms/c1.js. You can see that the module contains the function`run` that accepts the arguments via `kwargs`. The function will also only return `True` or `False`.
```
import re

def run(**kwargs):
    reg1 = r'function ant_cockroach'
    reg2 = r'cc_number'
    reg3 = r'payment_checkout[0-9]'
    script = kwargs.get('script', '')
    ant_cockroach = len(re.findall(reg1, script)) > 0
    cc_number = len(re.findall(reg2, script)) > 0
    checkout = len(re.findall(reg3, script)) > 0
    return ant_cockroach and cc_number and checkout
```
