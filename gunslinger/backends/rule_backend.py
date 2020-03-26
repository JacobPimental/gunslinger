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
        here = os.path.abspath(os.getcwd())
        return os.path.join(here, directory)


    def run_rules(self, **kwargs):
        for plugin_name in self._source.list_plugins():
            rule = self._source.load_plugin(plugin_name)
            try:
                is_mage = rule.run(**kwargs)
                if is_mage:
                    return True
            except Exception:
                print(f'Cannot run rule {plugin_name} ' \
                      '(possibly formatted incorrectly)')
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        rule_dir = '.'
    else:
        rule_dir = sys.argv[1]
    args = {'plugin_dir':rule_dir}
    rule_backend = RuleManager(**args)
    rule_backend.run_rules(**{'file':'yus'})
