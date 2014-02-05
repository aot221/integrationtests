"""
<Program Name>
  test_invalid_input.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  A battery of tests to run against the XML-RPC of the Custom Installer
  Builder, testing its ability to detect invalid input. Requires the Seattle
  integration test libraries, which should be in the Python path. The
  corresponding 'seattle_gmail_info' file should be present in the directory in
  which this script is run.

  Note that the XMLRPC_PROXY_URL variable must be modified below.
"""

import sys
import xmlrpclib

import integrationtestlib
import send_gmail


# The URL of the XML-RPC interface. Note the trailing slash.
XMLRPC_PROXY_URL = 'https://custombuilder.poly.edu/custom_install/xmlrpc/'

# Email addresses which should be notified in case of failure, in addition to
# the default list. For example:
#     NOTIFY_LIST = ['user@example.com', 'user2@example.com']
NOTIFY_LIST = []

# We will want to access the proxy across several functions, so make it global.
XMLRPC_PROXY = None

# We'll store any errors in a dictionary and send them off at the end.
ERRORS = dict()





# Inserts an error into the ERRORS dictionary.
def log_error(function_name, message):
  if function_name not in ERRORS:
    ERRORS[function_name] = list()

  ERRORS[function_name].append(message)




# Serves the dual purpose of testing against valid input and verifying the
# return value is of the right type.
def test_valid_input(test_function, return_type, function_name):
  integrationtestlib.log(
    ('Verifying that the \'' + function_name + '\' function returns object of ' +
     'type \'' + return_type.__name__ + '\'...'))

  results = None

  try:
    results = test_function()
  except:
    log_error(function_name, 'Failed against valid input.')
    return False, None

  if not isinstance(results, return_type):
    log_error(function_name,
      ('Returned object of type \'' + type(results).__name__ +
       '\' rather than expected type \'' + return_type.__name__) + '\'.')
    return False, None

  return True, results





def test_invalid_input(test_function, function_name, reason_invalid):
  integrationtestlib.log(('Verifying that the \'' + function_name +
      '\' function fails against invalid input.'))

  try:
    test_function()
  except:
    # An error occurred, so the invalid input was detected.
    return True

  # We didn't want success here!
  log_error(function_name, 'Function succeded with invalid input: ' + reason_invalid)
  return False




def test_api_version():
  test_function = lambda: XMLRPC_PROXY.api_version()
  test_valid_input(test_function, str, 'api_version')

  # Any argument should cause problems...
  test_function = lambda: XMLRPC_PROXY.api_version('')
  test_invalid_input(test_function, 'api_version', 'extra argument')





def test_build_installers():
  vessels = [{'percentage': 80, 'owner': 'owner'}]
  test_function = lambda: XMLRPC_PROXY.build_installers(vessels)
  success, results = test_valid_input(test_function, dict, 'build_installers')

  # A user might not have their vessels add to 80%.
  vessels = [{'percentage': 100, 'owner': 'owner'}]
  test_function = lambda: XMLRPC_PROXY.build_installers(vessels)
  test_invalid_input(test_function, 'build_installers', 'vessels add to 100%')

  # A user might neglect to give all vessels an owner.
  vessels = [{'percentage': 80}]
  test_function = lambda: XMLRPC_PROXY.build_installers(vessels)
  test_invalid_input(test_function, 'build_installers', 'vessel lacks owner')

  # A user might give an invalid cryptographic key.
  vessels = [{'percentage': 80, 'owner': 'owner'}]
  user_data = {'owner': {'public_key': 'INVALID'}}
  test_function = lambda: XMLRPC_PROXY.build_installers(vessels, user_data)
  test_invalid_input(test_function, 'build_installers', 'invalid cryptographic key')

  return success, results






def test_get_urls(build_id):
  test_function = lambda: XMLRPC_PROXY.get_urls(build_id)
  test_valid_input(test_function, dict, 'get_urls')

  # A user might give an invalid build ID.
  test_function = lambda: XMLRPC_PROXY.get_urls('INVALID')
  test_invalid_input(test_function, 'get_urls', 'invalid build ID')

  # A user might give a build ID that (probably) does not exist.
  test_function = lambda: XMLRPC_PROXY.get_urls('0123456789012345678901234567890123456789')
  test_invalid_input(test_function, 'get_urls', 'non-existent build ID')





def report_results():
  # If there are no entries in the dictionary, then no errors occurred.
  if len(ERRORS) == 0:
    integrationtestlib.log('All tests successful!')
    return

  # Otherwise, errors occurred...
  error_string = 'The following errors occurred:\n'

  for function in ERRORS:
    for error in ERRORS[function]:
      error_string += '\n[' + function + '] ' + error


  integrationtestlib.log(error_string)
  integrationtestlib.notify(error_string, 'Custom Installer Builder test failure')





def run_tests():
  test_results = dict()

  test_api_version()
  success, results = test_build_installers()

  if success:
    test_get_urls(results['build_id'])





def main():
  # Make the XML-RPC proxy accessible across the whole program.
  global XMLRPC_PROXY

  # Each test can reuse this proxy.
  XMLRPC_PROXY = xmlrpclib.ServerProxy(XMLRPC_PROXY_URL)


  # Setup the integration test library.
  success, explanation = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log('Failed to execute init_gmail(): ' + explanation)
    sys.exit(1)

  # Add any extra error log recipients.
  #integrationtestlib.notify_list=['monzum@gmail.com']
  integrationtestlib.notify_list.extend(NOTIFY_LIST)


  # The main event!
  run_tests()
  report_results()



if __name__ == '__main__':
  main()
