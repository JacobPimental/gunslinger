import gc
from bs4 import BeautifulSoup
import requests
import logging

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
    soup = BeautifulSoup(r.text, "lxml")
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
                #script=r.text)
            if fired_rules:
                scripts_found.append({'url':url,
                                      'fired_rules':fired_rules})
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
    report_data = {}
    for url in urls:
        js_urls = url_thread(url, timeout)
        found_scripts = get_js_content(js_urls, rule_manager, timeout)
        if found_scripts:
            report_data[url] = {'found_scripts':found_scripts}
        else:
            del found_scripts
    return report_data
