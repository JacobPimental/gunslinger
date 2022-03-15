import requests
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class URLScanProcessor():

    def __init__(self, config_data, rule_manager):
        api_key = config_data.get('api_key', '')
        self.header = {'Content-Type': 'application/json',
                       'Api-Key': api_key}
        self.rule_manager = rule_manager


    def parse_search_results(self, results):
        """Parses the results of the search to look for magecart.

        Arguments:
            results (array): Array of object results from URLScan
        """
        report_data = {'results':[]}

        for result in results:
            try:
                # Contains the URLScan info for URL
                url = result.replace('<', '').replace('>', '')
                web_requests, submitted_url, urlscan_url = self.get_requests(url)
                scripts_found = self.parse_requests_mp(web_requests)

                if scripts_found:
                    for script_data in scripts_found:
                        report = script_data
                        report['submitted_url'] = submitted_url
                        report['urlscan_url'] = urlscan_url
                        report_data['results'].append(report)
            except Exception as e:
                logger.error(e)

                continue
        if report_data['results']:
            return report_data
        return None


    def get_requests(self, url):
        """Gets the requests a URL makes when a webpage is loaded

        Arguments:
            url (string): Url of the URLScan page for the scanned website

        Returns:
            array: Array of request objects from URLScan API
            dict: Dict containing the original URL submitted to URLScan
                  and the URLScan report
        """
        logging.debug(f"Getting url: {url}")
        result_dat = requests.get(url, headers=self.header, timeout=10).json()
        logging.debug(f'Results: {result_dat}')
        if not 'data' in result_dat.keys() or not 'task' in result_dat.keys():
            return ([], '', '')
        submitted_url = result_dat['task']['url']
        urlscan_url = result_dat['task']['reportURL']

        return result_dat['data']['requests'], submitted_url, urlscan_url


    def get_response(self, h, response):
        """Gets the data returned from a request made by a webpage.

        Arguments:
            h (str): Hash of the response, used to get the url for the response
                from URLScan

        Returns:
            string: The data returned by the request (i.e. scripts, html, etc.)
        """
        print(f'Getting hash {h}')
        script = ''
        url = f'https://urlscan.io/responses/{h}/' #URLScan response URL
        script_r = requests.get(url, timeout=5)
        if script_r.status_code == 200:
            script = script_r.text
            fired_rules = self.rule_manager.run_rules(script=script, response_data=response)
            if fired_rules:
                return {'url':response['response']['url'], 'hash':h, 'fired_rules':fired_rules}
        return None


    def parse_requests(self, requests):
        """Parses the requests made by a webpage to look for Magecart.

        Arguments:
            requests (array): Array of objects contianing data on the request
                made
        """
        scripts_found = []

        for request in requests:
            try:
                response = request['response'] #Get the response for each request
                logging.debug(f'Got response: {response}')
                h = response['hash']
                script = self.get_response(response, h)
                url = response['response']['url']
                fired_rules = self.rule_manager.run_rules(script=script,
                                                          response_data=response)

                if fired_rules:
                    logger.info(f'Rule fired on {url}')
                    script_data = {'url':url, 'hash':h,
                                   'fired_rules':fired_rules}
                    scripts_found.append(script_data)
            except Exception as e:
                logger.error(f'URLScan Processor - parse_requests: {e}')

                continue
        return scripts_found


    def parse_requests_mp(self, requests):
        hashes = [r['response']['hash'] for r in requests if 'response' in r.keys() and 'hash' in r['response'].keys()]
        response_data = [r['response'] for r in requests if 'response' in r.keys() and 'hash' in r['response'].keys()]
        scripts = []
        executor = ThreadPoolExecutor(max_workers=50)
        scripts += list(executor.map(lambda h, r:self.get_response(h, r), hashes, response_data))
        while(None in scripts):
            scripts.remove(None)
        print(scripts)
        return scripts

def run(**kwargs):
    config_data = kwargs.get('config_info')
    rule_manager = kwargs.get('rule_manager')
    urlscan_processor = URLScanProcessor(config_data, rule_manager)
    rule_data = urlscan_processor.parse_search_results(kwargs.get('data',
                                                                  []))

    return rule_data
