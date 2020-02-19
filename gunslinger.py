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


    def get_results(self):
        """Gets results of search from URLScan

        Returns:
            array: Array of objects containing search results
        """
        search_results = requests.get('https://urlscan.io/api/v1/search/',
                                      headers=self.header,
                                      params=self.payload)
        try:
            search_dat = search_results.json()
            return search_dat.get('results',[])
        except Exception as e:
            print(e)
            return []


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
        """Sepecifically looking for javascript because magecart."""
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
            reg1 = r'([0-9A-Z]{3,})\1'
            reg2 = r'function [a-zA-Z]{3}\(\)'
            results = set(re.findall(reg1, script, flags=re.IGNORECASE))
            top_hit = max([script.count(r) for r in results])
            function_true = len(re.findall(reg2, script, flags=re.IGNORECASE)) > 0
            if top_hit > 30 and function_true:
                return True
            return False
        except Exception as e:
            return False


    def parse_search_results(self, results):
        """Parses the results of the search to look for magecart.

        Arguments:
            results (array): Array of object results from URLScan
        """
        for result in results:
            try:
                url = result['result'] #Contains the URLScan info for URL
                print(f'Checking {url}')
                requests = self.get_requests(url)
                self.parse_requests(requests)
            except Exception as e:
                print(e)
                continue


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
                if lst_time >= prev_time:
                    r = r[:i+1]
                    prev_time = cur_time
                    break
        else:
            prev_time = cur_time
        return (r, prev_time)


    def run(self):
        """Starts the application."""
        print('“The man in black fled across the desert, and the ' \
              'gunslinger followed.”')
        print('\t― Stephen King, The Gunslinger')
        prev_time = None
        while True:
            print('Getting results')
            r = self.get_results()
            if len(r) == 0:
                continue
            r, prev_time = self.remove_repeated_results(r, prev_time)
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
