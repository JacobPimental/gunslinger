import time
import argparse
from datetime import datetime as dt, timedelta as td
import json
import yaml
import os
import logging
from backends.slack_backend import Slack_MQ
from backends.sqs_backend import AWS_SQS
from backends.plugin_backend import PluginManager
import backends.processors as ProcessorManager
import backends.outputs as OutputManager

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
        self.config_info = self.read_config_file(kwargs.get('config_file'))
        rule_directory = self.config_info.get('rule_dir', '.')
        self.rule_manager = PluginManager(package='gunslinger.rules',
                                         plugin_dir=rule_directory)
        queue_data = self.config_info.get('queue_data', {})
        self.message_queue = Slack_MQ(**queue_data)


    def read_config_file(self, config_file):
        here = os.path.abspath(os.getcwd())
        config_path = os.path.join(here, config_file)
        try:
            with open(config_path) as f:
                config_data = yaml.load(f, Loader=yaml.FullLoader)
                return config_data
        except FileNotFoundError:
            logging.critical("Config file not found")
            exit()


    def check_if_mage(self, rule_data):
        """Checks if script is magecart based on regex.

        Arguments:
            script (string): Javascript to run regexes on

        Returns:
            boolean: True if regexes match, false if not
        """
        try:
            return self.rule_manager.run_rules(**rule_data)
        except Exception as e:
            logging.error(e)
            return False


    def report(self, report_data):
        """Reports on urls that rules fired on.

        Arguments:
            report_data (dict): dictionary of data to report on
        """
        for output in self.config_info['outputs']:
            output_name = output['name']
            OutputManager.run_output(output_name,
                                     report_data,
                                     output)
        del report_data

    def parse_message(self, data):
        processor_name = data.get('processor', '')
        if not processor_name:
            return
        logging.info(f'Loading processor {processor_name}')
        processor_data = data.get('data', {})
        config_info = self.config_info.get(processor_name, {})
        returned_data = ProcessorManager.run_processor(processor_name,
                                                       processor_data,
                                                       config_info,
                                                       self.rule_manager)
        if returned_data:
            self.report(returned_data)


    def run(self):
        """Starts the application."""
        logging.info('“The man in black fled across the desert, and the ' \
              'gunslinger followed.”')
        logging.info('\t― Stephen King, The Gunslinger')
        prev_time = 0
        latest = dt.now().timestamp()
        while True:
            data, prev_time = self.message_queue.get_next_message(
                oldest=prev_time,
                latest=latest)
            latest = (dt.fromtimestamp(float(prev_time)) + td(hours=1)).timestamp()
            if dt.fromtimestamp(latest) > dt.now():
                latest = dt.now().timestamp()
            elif prev_time == 0:
                latest = dt.now().timestamp()
            try:
                json_data = json.loads(data)
                self.parse_message(json_data)
            except Exception as e:
                logging.error(e)
                logging.info('Sleeping')
                time.sleep(self.config_info['queue_data'].get('rate_limit', 0))
                continue


if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.mkdir('logs')
    pid = os.getpid()
    logging.getLogger(__name__)
    logging.basicConfig(filename=f'logs/gunslinger_{pid}.log',
                        level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file',
                        help='Path to config file (default: gunslinger.yaml)',
                        default='gunslinger.yaml')
    args = parser.parse_args()
    gunslinger = Gunslinger(**vars(args))
    gunslinger.run()
