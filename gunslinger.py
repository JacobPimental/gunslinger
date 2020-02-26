import time
import re
import requests
import json
import slack
import argparse
import yaml
from datetime import datetime as dt

class Gunslinger():
    """Main class for Gunslinger application.

    Attributes:
        header (dict): Header for communication with URLScan API
        payload (dict): Search parameters for URLScan API
        client (slack WebClient): Used to integrate with Slack API

    Arguments:
        urlscan_key (string): API key for urlscan
        slack_token (string): Slack token for channel you want to send data to
        query (string, optional): Query you want to use against URLScan
        num_results (int, optional): Number of search results to return
    """

    def __init__(self, **kwargs):
        #if kwargs['config']:
        #    data = self.parse_yaml(kwargs['config'])
        #else:
        data = kwargs
        api_key = data['urlscan_key']
        slack_token = data['slack_token']
        query = data.get('query', '*')
        num_results = data.get('num_results', 100)
        api_key = kwargs['urlscan_key']
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        self.payload = {'q':query,
                        'size':num_results,
                        'sort':'time'}
        self.client = slack.WebClient(token=slack_token)
        self.channel = self.get_channel(data.get('queue_channel', 'mq'))


    def get_channel(self, channel):
        channels = self.client.conversations_list()
        for c in channels['channels']:
            if c['name'] == channel:
                return c['id']
        raise Exception('Channel does not exist')


    def parse_yaml(self, filename):
        """Reads necessary data from YAML file.

        Arguments:
            filename (string): Name of yaml file to parse

        Reutrns:
            dict: Parsed data from yaml file
        """
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
            return f

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
        """Specifically looking for javascript because magecart."""
        if ('mimeType' in response.keys() and
            response['mimeType'] == 'application/javascript'):
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
                    self.client.chat_postMessage(channel='#logging',
                                                 text=url)
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
            reg1 = r'([0-9A-Z]{3,})\1{3,}'
            reg2 = r'function [a-zA-Z]{3}\(\)'
            results = set(re.findall(reg1, script, flags=re.IGNORECASE))
            top_hit = max([script.count(r) for r in results])
            function_true = len(re.findall(reg2, script, flags=re.IGNORECASE)) > 0
            if top_hit > 2 and function_true:
                return True
            return False
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
                """Contains the URLScan info for URL"""
                url = result.replace('<','').replace('>','')
                print(f'Checking {url}')
                requests = self.get_requests(url)
                self.parse_requests(requests)
            except Exception as e:
                print(e)
                continue


    def get_results(self, prev_time):
        try:
            data = self.client.conversations_history(channel=self.channel,
                                                     limit=1000,
                                                     oldest=prev_time)
            messages = data.data['messages']
            for i in range(len(messages)-1):
                m = messages[i]
                if 'reactions' in messages[i+1] and 'New batch' in m['text'] \
                   and not 'reactions' in m.keys():
                    ts = m['ts']
                    self.client.reactions_add(channel=self.channel,
                                              name='+1',
                                              timestamp=ts)
                    prev_time = ts
                    dat = m['text'].strip().split('\n')[1:]
                    return dat, prev_time
                elif 'reactions' in m.keys():
                    return [], 0
            if 'reactions' in messages[i] and 'New batch' in \
               messages[i]['text']:
                ts=messages[i]['ts']
                self.client.reactions_add(channel=self.channel,
                                          name='+1',
                                          timestamp=ts)
                prev_time = ts
                dat = m['text'].strip().split('\n')[1:]
                return dat, prev_time
            else:
                return [], 0
        except Exception as e:
            print(e)
            time.sleep(60)
            return [],0


    def run(self):
        """Starts the application."""
        print('“The man in black fled across the desert, and the ' \
              'gunslinger followed.”')
        print('\t― Stephen King, The Gunslinger')
        prev_time = 0
        while True:
            print('Getting results')
            r,prev_time = self.get_results(prev_time)
            if len(r) == 0:
                time.sleep(15)
                continue
            print(r)
            print(r[0].replace('<','').replace('>',''))
            self.parse_search_results(r)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #group = parser.add_mutually_exclusive_group(required=True)
    #group.add_argument('-c','--config', help='YAML file containing config info')

    parser.add_argument('-u', '--urlscan_key', help='URLScan API key',
                        required=True)
    parser.add_argument('-s', '--slack_token', help='Slack Token',
                        required=True)
    parser.add_argument('-q', '--query', help='URLScan query (optional)',
                        default='*')
    parser.add_argument('-n', '--num_results',
                        help='Number of results to go through per iteration',
                        type=int, default=100)
    args = parser.parse_args()
    #print(vars(args))
    gunslinger = Gunslinger(**vars(args))
    gunslinger.run()
