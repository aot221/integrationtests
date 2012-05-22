"""
<Program>
  test_vessel_acquire_renew_release.py

<Started>
  03/01/2012

<Author>
  Sushant Bhadkamkar
  sushant@nyu.edu

<Purpose>
  A script to periodically test acquisition, renewal and release of resources 
  using Seattle's XMLRPC interface.
  Sends out an email to Seattle admins if any of the xmlrpc requests fail due 
  to connection errors or in case of resource acquisition failures.

<Usage>
  An example crontab entry for running this script every hour would be:
  
  0 * * * * /home/seattle/integrationtests/test_vessel_acquire_renew_release.py >
  /home/seattle/integrationtests/cron_log.test_vessel_acquire_renew_release
"""


import time
import sys

import seattleclearinghouse_xmlrpc
import integrationtestlib
import send_gmail


USERNAME = 'your_username'
PRIVATE_KEY_FILE = USERNAME + '.privatekey'
ALLOW_SSL_INSECURE = False

# Maximum number of resources to acquire
MAX_RESOURCES = 2


def init():
  """
  Returns an XMLRPC Client instance for a valid username and privatekey,
  sets up the mail notification system
  """
  try:
    private_key_string = open(PRIVATE_KEY_FILE).read()
  except IOError:
    print 'Please provide a valid private key file. You may obtain a ' + \
            'private key by registering a new account on the SeattleGENI website.'
    sys.exit(1)

  try:
    client = seattleclearinghouse_xmlrpc.SeattleClearinghouseClient(username=USERNAME,
               private_key_string=private_key_string,
               allow_ssl_insecure=ALLOW_SSL_INSECURE)

    success, msg = send_gmail.init_gmail()
    if not success:
      raise Exception(msg)
    return client
  except Exception, e:
    _log('SeattleGENI test failed. Error: ' + str(e))
    sys.exit(2)



def test_acquire_resources(client):
  """
  Returns a list of handles of vessels currently owned by the user.
  """
  vessel_handle_list = []

  # If previous call to release_resources failed, client may already have a few
  # acquired resources, we'll try to release them in this iteration
  acquired_resources_list = _do_call(client.get_resource_info)
  if acquired_resources_list:
    for resource in acquired_resources_list:
      vessel_handle_list.append(resource['handle'])
    
  newly_acquired_resources_list = _do_call(client.acquire_random_resources,
                                 MAX_RESOURCES)
  if newly_acquired_resources_list:
    for resource in newly_acquired_resources_list:
      vessel_handle_list.append(resource['handle'])

  return vessel_handle_list



def test_renew_resources(client, vessel_handle_list):
  _do_call(client.renew_resources, vessel_handle_list)



def test_release_resources(client, vessel_handle_list):
  _do_call(client.release_resources, vessel_handle_list)



def _do_call(function, *args):
  """
  Notify admins if there is a CommunicationError or a 
  UnableToAcquireResourcesError. Log all other low severity errors.
  """
  fname = function.__name__
  try:
    return function(*args)
  except seattleclearinghouse_xmlrpc.CommunicationError, e:
    msg = 'Method ' + fname + ' failed. Error: ' + str(e)
    _notify_admins(msg)
  except seattleclearinghouse_xmlrpc.UnableToAcquireResourcesError, e:
    msg = 'Failed to acquire resources. Error: ' + str(e)
    _notify_admins(msg)
  except Exception, e:
    msg = 'Method ' + fname + ' failed. Error: ' + str(e)
    _log(msg)



def _log(msg):
  integrationtestlib.log(msg)



def _notify_admins(msg):
  subject = 'SeattleGENI test failed.'
  integrationtestlib.notify(msg, subject)



def run_tests():
  client = init()
  
  vessel_handle_list = test_acquire_resources(client)
  if vessel_handle_list:
    test_renew_resources(client, vessel_handle_list)
    test_release_resources(client, vessel_handle_list)

  

if __name__ == '__main__':
  run_tests()
