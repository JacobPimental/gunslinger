import yaml
from backends.plugin_backend import PluginManager


class Gunslinger():
    """Main class for Gunslinger application.

    Attributes:
        config_info (dict): Information from config file
        rule_manager (PluginManager): Manages and runs the rule plugin files
        proc_manager (PluginManager): Manages and runs processor plugin files
        out_manager (PluginManager): Manages and runs output plugin files
    """

    def __init__(self):
        self.config_info = self.read_config_file()
        self.rule_manager = PluginManager(package='gunslinger.rules',
                                          plugin_dir=self.config_info.get('rule_dir', 'rules'))
        self.proc_manager = PluginManager(package='gunslinger.proc',
                                          plugin_dir='./backends/processors')
        self.out_manager = PluginManager(package='gunslinger.out',
                                         plugin_dir='./backends/outputs')

    def read_config_file(self):
        print('Reading log file...')
        with open('gunslinger.yaml') as f:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
            return config_data

    def parse_message(self, event):
        print('Parsing message')
        processor_name = event.get('processor', '')
        if not processor_name:
            return
        data = event.get('data', {})
        print(data)
        proc_config = self.config_info.get(processor_name, {})
        return_data = self.proc_manager.run_processor(
            processor_name, data, proc_config, self.rule_manager
        )
        print(return_data)
        if return_data:
            self.report(return_data)

    def report(self, data):
        for output in self.config_info['outputs']:
            output_name = output['name']
            print(output_name)
            self.out_manager.run_output(
                output_name, data, output
            )