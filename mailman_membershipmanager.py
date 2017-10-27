from urllib.parse import parse_qs
from mailmanclient import Client
import json
import hashlib



def successful_response(start_response, succeded, failed):
    if len(succeded) == 0 and len(failed) > 0:
        response = {'status': 'failed', 'reason': 'All operations failed.'}
    else:
        response = {'status': 'ok'}
        
    response['succeded'] = succeded
    response['failed'] = failed
        
    start_response('200 OK', [('content-type', 'application/json')])
    return [json.dumps(response).encode()]



def failed_response(start_response, statuscode, reason):
    response = {'status': 'failed', 'reason': reason}
        
    start_response(statuscode, [('content-type', 'application/json')])
    return [json.dumps(response).encode()]



def add_addresses(start_response, mailinglist, addresses):
    failed = []
    succeded = []
    
    for address in addresses:
        try:
            mailinglist.subscribe(address, pre_verified=True, pre_confirmed=True, pre_approved=True)
            succeded.append({'address': address})
        except Exception as err:
            failed.append({'address': address, 'reason': str(err) })

    return successful_response(start_response, succeded, failed)



def remove_addresses(start_response, mailinglist, addresses):
    failed = []
    succeded = []
    
    for address in addresses:
        try:
            mailinglist.unsubscribe(address)
            succeded.append({'address': address})
        except Exception as err:
            failed.append({'address': address, 'reason': str(err) })

    return successful_response(start_response, succeded, failed)



def clear_addresses(start_response, mailinglist):
    for member in mailinglist.members:
        member.unsubscribe()

    return successful_response(start_response, [], [])



def replace_addresses(start_response, mailinglist, old, new):
    failed = []
    succeded = []

    # Remove old adresses
    for address in old:
        try:
            mailinglist.unsubscribe(address)
            succeded.append({'address': address})
        except Exception as err:
            failed.append({'address': address, 'reason': str(err) })

    # Add new adresses
    for address in new:
        try:
            mailinglist.subscribe(address, pre_verified=True, pre_confirmed=True, pre_approved=True)
            succeded.append({'address': address})
        except Exception as err:
            failed.append({'address': address, 'reason': str(err) })

    return successful_response(start_response, succeded, failed)



def replace_all_addresses(start_response, mailinglist, addresses):
    failed = []
    succeded = []

    for member in mailinglist.members:
        member.unsubscribe()
        
    for address in addresses:
        try:
            mailinglist.subscribe(address, pre_verified=True, pre_confirmed=True, pre_approved=True)
            succeded.append({'address': address})
        except Exception as err:
            failed.append({'address': address, 'reason': str(err) })

    return successful_response(start_response, succeded, failed)



# May throw any exception
def get_post_data(environ):
    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    
    request_body = environ['wsgi.input'].read(request_body_size)
    form_data = parse_qs(request_body)
    
    json_data = form_data[b"data"][0]
    signature = form_data[b"signature"][0]

    data = json.loads(json_data.decode())

    # Make sure this key is available by accessing it
    tmp = data['mailinglist']

    data['raw'] = json_data;
    data['signature'] = signature

    if not 'addresses' in data:
        data['addresses'] = []
    if not 'add' in data:
        data['add'] = []
    if not 'remove' in data:
        data['remove'] = []
    
    return data



def get_config(filename):
    data = {}
    with open(filename) as data_file:
        data = json.load(data_file)
    return data



def verify_signature(mailinglist, data):
    return data['signature'].lower() == hashlib.sha512(data['raw'] + mailinglist['authkey'].encode()).hexdigest().lower().encode()

def check_authorisation(config, data):
    for mailinglist in config['lists']:
        if mailinglist['listaddress'] == data['mailinglist']:
            if verify_signature(mailinglist, data):
                return True
    return False



def app(environ, start_response):
    # Verify HTTP method
    if environ['REQUEST_METHOD'] != 'POST':
        return failed_response(start_response, '405 Method Not Allowed', "Method Not Allowed: " + environ['REQUEST_METHOD'])

    # Obtain POST data
    try:
        data = get_post_data(environ)
    except Exception as err:
        return failed_response(start_response, '400 Bad Request', "Data error: " + str(err))

    # Verify signature of POST data
    config = get_config("config.json")
    if not check_authorisation(config, data):
        return failed_response(start_response, '403 Forbidden', "Could not verify authentication")

    # Get mailinglist from Mailman API
    client = Client(config['resturl'], config['restadmin'], config['restpass'])
    try:
        mailinglist = client.get_list(data['mailinglist'])
    except Exception as err:
        return failed_response(start_response, '422 Unprocessable Entity', "Mailman error (" + data['mailinglist'] + "): " + str(err))

    # Dispatch to API endpoints
    if environ['PATH_INFO'] == '/add':
        return add_addresses(start_response, mailinglist, data['addresses'])
    elif environ['PATH_INFO'] == '/remove':
        return remove_addresses(start_response, mailinglist, data['addresses'])
    elif environ['PATH_INFO'] == '/clear':
        return clear_addresses(start_response, mailinglist)
    elif environ['PATH_INFO'] == '/replace':
        return replace_addresses(start_response, mailinglist, data['remove'], data['add'])
    elif environ['PATH_INFO'] == '/replace_all':
        return replace_all_addresses(start_response, mailinglist, data['addresses'])
    else:
        return failed_response(start_response, '404 Not Found', environ['PATH_INFO'] + " was not found.")

