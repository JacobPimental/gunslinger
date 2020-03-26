import time
import re
import requests
import json
import slack
import argparse
import yaml
from datetime import datetime as dt, timedelta as td
from backends.slack_backend import Slack_MQ
from backends.sqs_backend import AWS_SQS
from backends.rule_backend import RuleManager

class Gunslinger():
    """Main class for Gunslinger application.

    Attributes:
        header (dict): Header for communication with URLScan API
        payload (dict): Search parameters for URLScan API

    Arguments:
        urlscan_key (string): API key for urlscan
        slack_token (string): Slack token for channel you want to send data to
        query (string, optional): Query you want to use against URLScan
        num_results (int, optional): Number of search results to return
    """

    def __init__(self, **kwargs):
        # Slack API info
        slack_token = kwargs.get('slack_token', '')
        queue_channel = kwargs.get('queue_channel', 'mq')
        # SQS API info
        sqs_url = kwargs.get('sqs_url', '')
        # UrlScan API info
        api_key = kwargs['urlscan_key']
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        # Rule Plugin Info
        rule_directory = kwargs.get('rule_dir', '.')
        self.rule_manger = RuleManager(package='gunslinger.rules',
                                       plugin_dir=rule_directory)
        if slack_token and not sqs_url:
            self.rate_limit = 15
            self.message_queue = Slack_MQ(slack_token, queue_channel)
        elif sqs_url:
            self.rate_limit = 0
            self.message_queue = AWS_SQS(sqs_url)
        self.slack_backend = Slack_MQ(slack_token)


    def get_requests(self, url):
        """Gets the requests a URL makes when a webpage is loaded

        Arguments:
            url (string): Url of the URLScan page for the scanned website

        Returns:
            array: Array of request objects from URLScan API
        """
        result_dat = requests.get(url, headers=self.header).json()
        if not 'data' in result_dat.keys():
            return []
        return result_dat['data']['requests']


    def get_response(self, response, h):
        """Gets the data returned from a request made by a webpage.

        Arguments:
            response (dict): URLScan response object
            h (str): Hash of the response, used to get the url for the response
                from URLScan

        Returns:
            string: The data returned by the request (i.e. scripts, html, etc.)
        """
        script = ''
        response = response['response']
        print(f'Getting hash {h}')
        # Specifically looking for javascript because magecart.
        if 'mimeType' in response.keys() and \
                response['mimeType'] == 'application/javascript':
            url = f'https://urlscan.io/responses/{h}/' #URLScan response URL
            script_r = requests.get(url)
            if script_r.status_code == 200:
                script = script_r.text
        return script


    def parse_requests(self, requests):
        """Parses the requests made by a webpage to look for Magecart.

        Arguments:
            requests (array): Array of objects contianing data on the request
                made
        """
        print(len(requests))
        for request in requests:
            try:
                response = request['response'] #Get the response for each request
                h = response['hash']
                script = self.get_response(response, h)
                url = response['response']['url']
                print(f'Checking: {url}')
                if self.check_if_mage(script):
                    self.slack_backend.post_message(url, channel='#logging')
                    print(url)
            except Exception as e:
                continue

    def check_if_mage(self, script):
        """Checks if script is magecart based on regex.

        Arguments:
            script (string): Javascript to run regexes on

        Returns:
            boolean: True if regexes match, false if not
        """
        try:
            return self.rule_manger.run_rules(script=script)
        except Exception as e:
            print(e)
            return False


    def parse_search_results(self, results):
        """Parses the results of the search to look for magecart.

        Arguments:
            results (array): Array of object results from URLScan
        """
        for result in results:
            try:
                # Contains the URLScan info for URL
                url = result.replace('<', '').replace('>', '')
                print(f'Checking {url}')
                web_requests = self.get_requests(url)
                self.parse_requests(web_requests)
            except Exception as e:
                print(e)
                continue


    def run(self):
        """Starts the application."""
        print('“The man in black fled across the desert, and the ' \
              'gunslinger followed.”')
        print('\t― Stephen King, The Gunslinger')
        prev_time = 0
        latest = dt.now().timestamp()
        while True:
            print('Getting results')
            results, prev_time = self.message_queue.get_next_message(
                oldest=prev_time,
                latest=latest)
            latest = (dt.fromtimestamp(float(prev_time)) + td(hours=1)).timestamp()
            if dt.fromtimestamp(latest) > dt.now():
                latest = dt.now().timestamp()
            elif prev_time == 0:
                latest = dt.now().timestamp()
            if len(results) == 0:
                time.sleep(self.rate_limit)
                continue
            self.parse_search_results(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--urlscan_key', help='URLScan API key',
                        required=True)
    parser.add_argument('-a', '--sqs_url', help='URL of AWS SQS service')
    parser.add_argument('-c', '--queue_channel', help='Message Queue Channel')
    parser.add_argument('-s', '--slack_token', help='Slack Token',
                        required=True)
    parser.add_argument('-d', '--rule_dir',
                        help='Directory containing python plugins ' \
                             'to be used as rules',
                        default='')
    parser.add_argument('-q', '--query', help='URLScan query (optional)',
                        default='*')
    args = parser.parse_args()
    gunslinger = Gunslinger(**vars(args))
    gunslinger.run()
