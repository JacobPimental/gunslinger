import requests
import logging

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
        report_data = []
        for result in results:
            try:
                # Contains the URLScan info for URL
                url = result.replace('<', '').replace('>', '')
                web_requests, submitted_url, urlscan_url = self.get_requests(url)
                report = self.parse_requests(web_requests)
                if report['scripts_found']:
                    report['submitted_url'] = submitted_url
                    report['urlscan_url'] = urlscan_url
                    report_data.append(report)
            except Exception as e:
                logger.error(e)
                continue
        return report_data


    def get_requests(self, url):
        """Gets the requests a URL makes when a webpage is loaded

        Arguments:
            url (string): Url of the URLScan page for the scanned website

        Returns:
            array: Array of request objects from URLScan API
            dict: Dict containing the original URL submitted to URLScan
                  and the URLScan report
        """
        result_dat = requests.get(url, headers=self.header, timeout=10).json()
        if not 'data' in result_dat.keys() or not 'task' in result_dat.keys():
            return ([], '', '')
        submitted_url = result_dat['task']['url']
        urlscan_url = result_dat['task']['reportURL']
        return result_dat['data']['requests'], submitted_url, urlscan_url


    def get_response(self, response, h):
        """Gets the data returned from a request made by a webpage.

        Arguments:
            response (dict): URLScan response object
            h (str): Hash of the response, used to get the url for the response
                from URLScan

        Returns:
            string: The data returned by the request (i.e. scripts, html, etc.)
        """
        logger.info(f'Getting hash {h}')
        script = ''
        response = response['response']
        url = f'https://urlscan.io/responses/{h}/' #URLScan response URL
        script_r = requests.get(url, timeout=10)
        if script_r.status_code == 200:
            script = script_r.text
        return script


    def parse_requests(self, requests):
        """Parses the requests made by a webpage to look for Magecart.

        Arguments:
            requests (array): Array of objects contianing data on the request
                made
        """
        report_data = {'scripts_found': []}
        for request in requests:
            try:
                response = request['response'] #Get the response for each request
                h = response['hash']
                script = self.get_response(response, h)
                url = response['response']['url']
                fired_rules = self.rule_manager.run_rules(script=script,
                                                          response_data=response)
                if fired_rules:
                    logger.info(f'Rule fired on {url}')
                    script_data = {'url':url, 'hash':h,
                                   'fired_rules':fired_rules}
                    report_data['scripts_found'].append(script_data)
            except Exception as e:
                logger.error(e)
                continue
        return report_data

def run(**kwargs):
    config_data = kwargs.get('config_info')
    rule_manager = kwargs.get('rule_manager')
    urlscan_processor = URLScanProcessor(config_data, rule_manager)
    rule_data = urlscan_processor.parse_search_results(kwargs.get('data',
                                                                  []))
    return rule_data
