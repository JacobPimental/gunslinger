import requests
import slack
import base64 as b64
import argparse
from datetime import datetime as dt
from backends.slack_backend import Slack_MQ
from backends.sqs_backend import AWS_SQS

class Reloader():

    def __init__(self, **kwargs):
        data = kwargs
        # Slack API info
        slack_token = data.get('slack_token', '')
        queue_channel = data.get('queue_channel', 'mq')
        # SQS API info
        sqs_url = data.get('sqs_url', '')
        # UrlScan API info
        query = data.get('query', '*')
        num_results = data.get('num_results', 1000)
        api_key = kwargs['urlscan_key']
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        self.payload = {'q':query,
                        'size':num_results,
                        'sort':'time'}
        if slack_token:
            self.message_queue = Slack_MQ(slack_token, queue_channel)
        elif sqs_url:
            self.message_queue = AWS_SQS(sqs_url)


    def get_results(self):
        """Gets results of search from URLScan

        Returns:
            array: Array of objects containing search results
        """
        try:
            search_results = requests.get('https://urlscan.io/api/v1/search/',
                                          headers=self.header,
                                          params=self.payload)
            search_dat = search_results.json()
            return search_dat.get('results',[])
        except Exception as e:
            print(e)
            return []


    def remove_repeated_results(self, results, prev_time=None):
        """Removes previously parsed search results.

        Arguments:
            results (array): Array of results returned from URLScan
            prev_time (datetime): Default None; The time of the first result
                from the previous search query

        Returns:
            tuple: tuple containing: Array of objects containing results
                from URLScan search, now without previously scanned items,
                the new prev_time variable for use in the next iteration
        """
        r = results
        cur_time_s = r[0]['task']['time']
        cur_time = dt.strptime(cur_time_s, '%Y-%m-%dT%H:%M:%S.%fZ')
        if prev_time:
            i = len(r)
            while True:
                i -= 1
                lst_time_s = r[i]['task']['time']
                lst_time = dt.strptime(lst_time_s, '%Y-%m-%dT%H:%M:%S.%fZ')
                if lst_time > prev_time:
                    r = r[:i+1]
                    prev_time = cur_time
                    break
                elif i <= 0:
                    r = []
                    prev_time = cur_time
                    break
        else:
            prev_time = cur_time
        return (r, prev_time)


    def parse_search_results(self, results):
        """Sends a list of results to Slack MessageQueue for processing.

        Arguments:
            results (array): rray of object results from URLScan
        """
        text_data = ""
        for result in results:
            try:
                text_data += result['result']
                text_data += '\n'
            except Exception as e:
                print(e)
                continue
        if not text_data == "":
            header = 'New batch incoming:\n'
            msg = header+text_data
            self.message_queue.post_message(msg)


    def run(self):
        """Starts the application."""
        prev_time = None
        msg = 'The man in black fled across the desert, and the ' \
              'gunslinger followed\n\t- Stephen King, The Gunslinger'
        result = self.message_queue.post_message(msg, reaction='gun')
        while True:
            print('Getting results')
            r = self.get_results()
            if len(r) == 0:
                continue
            r, prev_time = self.remove_repeated_results(r, prev_time)
            self.parse_search_results(r)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--urlscan_key', help='URLScan API key',
                        required=True)
    parser.add_argument('-a', '--sqs_url', help='AWS SQS Url')
    parser.add_argument('-c', '--queue_channel', help='Message Queue Channel')
    parser.add_argument('-s', '--slack_token', help='Slack Token')
    parser.add_argument('-q', '--query', help='URLScan query (optional)',
                        default='*')
    parser.add_argument('-n', '--num_results',
                        help='Number of results to go through per iteration',
                        type=int, default=50)
    args = parser.parse_args()
    reloader = Reloader(**vars(args))
    reloader.run()
