from pluginbase import PluginBase
import os
import sys

class RuleManager():

    def __init__(self, **kwargs):
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
            rule = self._source.load_plugin(plugin_name)
            try:
                rule_fired = rule.run(**kwargs)
                if rule_fired:
                    fired_rules.append(plugin_name)
            except Exception:
                print(f'Cannot run rule {plugin_name} ' \
                      '(possibly formatted incorrectly)')
        return fired_rules
