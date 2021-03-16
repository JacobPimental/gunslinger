#!/bin/python3

import sys
import argparse
from datetime import datetime as dt
import os
import math
import json
import yaml
import logging

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)

from backends.slack_backend import Slack_MQ
from backends.sqs_backend import AWS_SQS

class Reloader():

    def __init__(self, **kwargs):
        self.config_info = self.read_config_file(kwargs.get('config_file'))
        data = self.config_info.get('inputs',
                                    {'urlscan_input': {}})['urlscan_input']
        # UrlScan API info
        self._query = data.get('query', '*')
        api_key = data.get('urlscan_key', '')
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        self.payload = {'size':10000,
                        'sort':'date'}
        self.prev_time = dt.utcnow()
        self.cron = data.get('cron', '* * * * *')
        self.num_workers = data.get('num_workers', 5)
        queue_type = self.config_info.get('message_queue', '')
        queue_data = self.config_info.get('queue_data', {})

        if queue_type == 'slack_mq':
            self.message_queue = Slack_MQ(**queue_data)
        elif queue_type == 'aws_sqs':
            self.message_queue = AWS_SQS(**queue_data)
        else:
            logging.critical('Error: No message queue specified!')
            sys.exit()


    def read_config_file(self, config_file):
        here = os.path.abspath(os.getcwd())
        config_path = os.path.join(here, config_file)
        try:
            with open(config_path) as f:
                config_data = yaml.load(f, Loader=yaml.FullLoader)

                return config_data
        except FileNotFoundError:
            logging.critical('config file not found')
            exit()


    def get_results(self, prev_time):
        """Gets results of search from URLScan

        Returns:
            array: Array of objects containing search results
        """
        try:
            past_time = prev_time.strftime(r'%Y-%m-%dT%H\:%M\:%S.%fZ')
            self.payload['q'] = f'({self._query}) AND date:>{past_time}'
            search_results = requests.get('https://urlscan.io/api/v1/search/',
                                          headers=self.header,
                                          params=self.payload)
            search_dat = search_results.json()
            results = search_dat.get('results', [])

            return results
        except Exception as e:
            logging.error(e)

            return []


    def parse_search_results(self, results):
        """Sends a list of results to Slack MessageQueue for processing.

        Arguments:
            results (array): rray of object results from URLScan
        """
        result_urls = [result.get('result') for result in results]
        div = math.ceil(len(result_urls) / self.num_workers)

        for i in range(self.num_workers):
            result_data = result_urls[i*div:(i+1)*div]

            if not result_data:
                continue
            processor_data = {'processor':'urlscan_processor',
                              'data': result_urls[i*div:(i+1)*div]}
            text_data = json.dumps(processor_data)

            if text_data != "":
                msg = text_data
                self.message_queue.post_message(msg)


    def search_job(self):
        """Job that runs to fetch the next set of URLScan results."""
        logging.info('Getting results')
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

        while True:
            scheduler.start()


if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.mkdir('logs')
    PID = os.getpid()
    logging.getLogger(__name__)
    logging.basicConfig(filename=f'logs/reloader_{PID}.log',
                        level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-c', '--config-file',
                        help='Path to config file (default: '\
                        'gunslinger.yaml)',
                        default='gunslinger.yaml')
    ARGS = PARSER.parse_args()
    RELOADER = Reloader(**vars(ARGS))
    RELOADER.run()
