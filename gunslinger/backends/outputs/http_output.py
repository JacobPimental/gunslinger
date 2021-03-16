import requests
import logging
import json

class HTTPOutputHandler():

    def __init__(self, **kwargs):
        logging.getLogger(__name__)
        try:
            self.headers = kwargs.get('headers', {})
            self.headers['content-type'] = 'application/json'
            self.fields = kwargs.get('fields', [])
            self.method = kwargs.get('method', 'POST')
            self.endpoint = kwargs['url']
        except Exception as exc:
            logging.critical(f'HTTP Output configured incorrectly: {exc}')


    def get_field(self, data, field):
        if isinstance(data, dict):
            if field in data.keys():
                yield data[field]
            else:
                for key in data.keys():
                    for val in self.get_field(data[key], field):
                        yield val
        elif isinstance(data, list):
            for dat in data:
                for val in self.get_field(dat, field):
                    yield val


    def create_data(self, data):
        if not 'results' in data:
            return
        num_results = len(data['results'])
        report_data = {'results':[{} for _ in range(num_results)]}
        for field in self.fields:
            field_data = list(self.get_field(data, field))
            print(field_data)
            if len(field_data) < num_results:
                field_data += [''] * (num_results - len(field_data))
            for i in range(num_results):
                print(field_data[i])
                report_data['results'][i][field] = field_data[i]
        return report_data


    def send_data(self, data):
        report_data = self.create_data(data)
        response = requests.request(self.method, self.endpoint,
                                    data=json.dumps(report_data),
                                    headers=self.headers)
        if not response.ok:
            status = response.status_code
            logging.error(f'ERROR sending data to {self.endpoint}: {status} :'\
                          ' {response.text}')


def run(output_data, config_info):
    http_handler = HTTPOutputHandler(**config_info)
    try:
        http_handler.send_data(output_data)
    except Exception as exc:
        logging.error(exc)
