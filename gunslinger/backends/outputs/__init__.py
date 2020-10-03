from . import slack_output
import logging

def run_output(output_name, output_data, config_info):
    logging.getLogger(__name__)
    try:
        if output_name == 'slack_output':
            slack_output.run(output_data,
                             config_info)
    except Exception as e:
        logging.error(e)
    return {}
