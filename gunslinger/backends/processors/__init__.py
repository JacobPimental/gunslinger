from . import urlscan_processor
from . import domain_processor
import logging

def run_processor(processor_name, processor_data, config_info, rule_manager):
    logging.getLogger(__name__)
    try:
        if processor_name == 'domain_processor':
            return domain_processor.run(data=processor_data,
                                        config_info=config_info,
                                        rule_manager=rule_manager)
        elif processor_name == 'urlscan_processor':
            return urlscan_processor.run(data=processor_data,
                                         config_info=config_info,
                                         rule_manager=rule_manager)
    except Exception as e:
        logging.error(e)
    return {}
