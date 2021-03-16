import time
import sys
import argparse
from datetime import datetime as dt, timedelta as td
import json
import os
import logging
import yaml
from backends.slack_backend import Slack_MQ
from backends.sqs_backend import AWS_SQS
from backends.plugin_backend import PluginManager

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
        processor_directory = self.config_info.get('processor_dir',
                                                   './backends/processors')
        self.proc_manager = PluginManager(package='gunslinger.processors',
                                          plugin_dir=processor_directory)
        out_dir = self.config_info.get('output_plugin_dir',
                                       './backends/outputs')
        self.out_manager = PluginManager(package='gunslinger.outputs',
                                         plugin_dir=out_dir)
        mq_type = self.config_info.get('message_queue', 'slack_mq')
        queue_data = self.config_info.get('queue_data', {})

        if mq_type == 'slack_mq':
            self.message_queue = Slack_MQ(**queue_data)
        elif mq_type == 'aws_sqs':
            self.message_queue = AWS_SQS(**queue_data)


    def read_config_file(self, config_file):
        here = os.path.abspath(os.getcwd())
        config_path = os.path.join(here, config_file)
        try:
            with open(config_path) as f:
                config_data = yaml.load(f, Loader=yaml.FullLoader)

                return config_data
        except FileNotFoundError:
            logging.critical("Config file not found")
            sys.exit()


    def report(self, report_data):
        """Reports on urls that rules fired on.

        Arguments:
            report_data (dict): dictionary of data to report on
        """

        for output in self.config_info['outputs']:
            output_name = output['name']
            self.out_manager.run_output(output_name,
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
        returned_data = self.proc_manager.run_processor(
            processor_name, processor_data,
            config_info, self.rule_manager)

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
