import gc
import logging
from bs4 import BeautifulSoup
import requests
import hashlib

logger = logging.getLogger(__name__)

def url_thread(url, timeout=10):
    clean_url = url.replace('<', '').replace('>', '')

    if '|' in clean_url:
        clean_url = clean_url[:clean_url.index('|')]

    if (not clean_url.startswith('http://') and not
            clean_url.startswith('https://')):
        clean_url = 'http://' + clean_url
    logger.info(f'Getting scripts at {clean_url}')
    r = requests.head(clean_url, allow_redirects=True,
                      timeout=timeout)

    if not 'text/html' in r.headers['Content-Type']:
        return []
    r = requests.get(clean_url, timeout=timeout)
    soup = BeautifulSoup(r.content.decode('ISO-8859-1')
                         , "lxml")
    scripts = soup.find_all('script', {'src':True})
    logger.info(f'Found {len(scripts)} at url')
    soup.decompose()
    data = [clean_url]

    for script in scripts:
        script_src = script['src']

        if script_src[:2] == '//':
            script_src = 'http:' + script_src
        elif (not script_src.startswith('http://') and not
              script_src.startswith('https://')):
            script_src = 'http://' + script_src
        data.append(script_src)
    logger.info(f'Got {len(data)} script(s)')

    return data


def get_js_content(js_dat, rule_manager, timeout=10):
    scripts_found = []

    for url in js_dat:
        logger.info(f'Getting script at {url}')
        try:
            r = requests.get(url, timeout=timeout)
            logger.info('Running rules')
            fired_rules = rule_manager.run_rules(
                script=r.content.decode('ISO-8859-1'))

            if fired_rules:
                sha256_hash = hashlib.sha256(r.content).hexdigest()
                scripts_found.append({'url':url,
                                      'fired_rules':fired_rules,
                                      'hash':sha256_hash})
        except Exception as e:
            logger.error(e)

            continue
        gc.collect()
        logger.info(f'Got script at {url}')

    return scripts_found


def run(**kwargs):
    urls = kwargs.get('data', [])
    timeout = kwargs.get('config_info',
                         {'timeout':10}).get('timeout', 10)
    rule_manager = kwargs.get('rule_manager')
    report_data = {'results':[]}

    for url in urls:
        js_urls = url_thread(url, timeout)
        found_scripts = get_js_content(js_urls, rule_manager, timeout)

        if found_scripts:
            for script_data in found_scripts:
                report = script_data
                report['submitted_url'] = url
                report_data['results'].append(report)
        else:
            del found_scripts
    if report_data['results']:
        return report_data
    return None
