import re

def run(**kwargs):
    print('Running Rule')
    reg1 = r'function ant_cockroach'
    reg2 = r'cc_number'
    reg3 = r'payment_checkout[0-9]'
    script = kwargs.get('script', '')
    ant_cockroach = len(re.findall(reg1, script)) > 0
    cc_number = len(re.findall(reg2, script)) > 0
    checkout = len(re.findall(reg3, script)) > 0
    return ant_cockroach and cc_number and checkout
