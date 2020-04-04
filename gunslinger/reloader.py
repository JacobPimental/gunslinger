import sys
import argparse
from datetime import datetime as dt, timedelta as td
import math

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

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
        self._query = data.get('query', '*')
        api_key = kwargs['urlscan_key']
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        self.payload = {'size':10000,
                        'sort':'date'}
        self.prev_time = dt.utcnow()
        self.cron = ' '.join(data['cron']).replace('_', '*')
        self.num_workers = data['num_workers']
        if slack_token:
            self.message_queue = Slack_MQ(slack_token, queue_channel)
        elif sqs_url:
            self.message_queue = AWS_SQS(sqs_url)
        else:
            print('Error: No message queue specified!')
            sys.exit()


    def get_results(self, prev_time):
        """Gets results of search from URLScan

        Returns:
            array: Array of objects containing search results
        """
        try:
            past_hour = prev_time.strftime(r'%Y-%m-%dT%H\:%M\:%S.%fZ')
            self.payload['q'] = self._query + f' AND date:>{past_hour}'
            search_results = requests.get('https://urlscan.io/api/v1/search/',
                                          headers=self.header,
                                          params=self.payload)
            search_dat = search_results.json()
            results = search_dat.get('results', [])
            return results
        except Exception as e:
            print(e)
            return []


    def parse_search_results(self, results):
        """Sends a list of results to Slack MessageQueue for processing.

        Arguments:
            results (array): rray of object results from URLScan
        """
        result_urls = [result.get('result') for result in results]
        div = math.ceil(len(result_urls) / self.num_workers)
        for i in range(self.num_workers):
            text_data = '\n'.join(result_urls[i*div:(i+1)*div])
            if text_data != "":
                msg = text_data
                self.message_queue.post_message(msg)


    def search_job(self):
        print('Getting results')
        search_results = self.get_results(self.prev_time)
        if len(search_results) == 0:
            return
        self.prev_time = dt.strptime(search_results[0]['task']['time'],
                                     '%Y-%m-%dT%H:%M:%S.%fZ')
        self.parse_search_results(search_results)


    def run(self):
        """Starts the application."""
        msg = 'The man in black fled across the desert, and the ' \
              'gunslinger followed\n\t- Stephen King, The Gunslinger'
        self.message_queue.post_message(msg, reaction='gun')
        scheduler = BlockingScheduler()
        scheduler.add_job(self.search_job, CronTrigger.from_crontab(self.cron))
        scheduler.start()


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-u', '--urlscan_key', help='URLScan API key',
                        required=True)
    PARSER.add_argument('-a', '--sqs_url', help='AWS SQS Url (optional)')
    PARSER.add_argument('-c', '--queue_channel', help='Message Queue Channel')
    PARSER.add_argument('-s', '--slack_token', help='Slack Token')
    PARSER.add_argument('-q', '--query', help='URLScan query (optional)',
                        default='*')
    PARSER.add_argument('-cr', '--cron',
                        help='Cron job for searches to run on ' \
                             '(Default: 0 _ _ _ _)',
                        type=str, default=['0', '_', '_', '_', '_'],
                        nargs=5)
    PARSER.add_argument('-w', '--num_workers',
                        help='Number of gunslinger works to divy tasks',
                        default=5, type=int)
    ARGS = PARSER.parse_args()
    RELOADER = Reloader(**vars(ARGS))
    RELOADER.run()
