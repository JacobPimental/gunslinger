# gunslinger
Gunslinger is used to hunt for Magecart sites using URLScan's API

## Usage
```
python gunslinger.py [-h] -u URLSCAN_KEY -s SLACK_TOKEN [-q QUERY] [-n NUM_RESULTS]

optional arguments:
  -h, --help            show this help message and exit
  -u URLSCAN_KEY, --urlscan_key URLSCAN_KEY
                        URLScan API key
  -s SLACK_TOKEN, --slack_token SLACK_TOKEN
                        Slack Token
  -q QUERY, --query QUERY
                        URLScan query (optional)
  -n NUM_RESULTS, --num_results NUM_RESULTS
                        Number of results to go through per iteration
```
