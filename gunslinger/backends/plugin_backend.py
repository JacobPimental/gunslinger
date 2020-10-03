from pluginbase import PluginBase
import os
import sys
import logging

class PluginManager():

    def __init__(self, **kwargs):
        logging.getLogger(__name__)
        package = kwargs.get('package', 'rule_backend.plugins')
        self._plugin_base = PluginBase(package=package)
        self._plugin_dir = kwargs.get('plugin_dir', '.')
        plugin_path = self.get_path(self._plugin_dir)
        self._source = self._plugin_base.make_plugin_source(
            searchpath=[plugin_path])


    def get_path(self, directory):
        """Gets path of rule directory relative to working directory.

        Arguments:
            directory (str): Path to the directory of rule files

        Returns:
            str: A string of the absolute path to the rule directory
        """
        here = os.path.abspath(os.getcwd())
        return os.path.join(here, directory)


    def run_rules(self, **kwargs):
        """Runs rules via python plugins.

        Returns:
            list: List of all rules that returned True
        """
        fired_rules = []
        for plugin_name in self._source.list_plugins():
            logging.info(f'Running rule {plugin_name}')
            rule = self._source.load_plugin(plugin_name)
            try:
                rule_fired = rule.run(**kwargs)
                if rule_fired:
                    fired_rules.append(plugin_name)
            except Exception as e:
                logging.error(f'Cannot run rule {plugin_name} ' \
                              '(possibly formatted incorrectly)')
                logging.error(e)
        return fired_rules


    def run_processor(self, processor_name, processor_data, config_info,
                      rule_manager):
        plugin = self._source.load_plugin(processor_name)
        try:
            returned_data = plugin.run(data=processor_data,
                                       config_info=config_info,
                                       rule_manager=rule_manager)
            return returned_data
        except Exception as e:
            logging.error(f'Cannot run processor {processor_name} ' \
                          '(possible misconfigured)')
            logging.error(e)
            return {}


    def run_output(self, output_name, output_data, config_info):
        plugin = self._source.load_plugin(output_name)
        try:
            plugin.run(output_data, config_info)
        except Exception as e:
            logging.error(f'Cannot run output {output_name} ' \
                          '(possibly misconfigured)')
            logging.error(e)
