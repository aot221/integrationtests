"""
<Program Name>
  test_build_installers.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  A battery of tests to run against the XML-RPC of the Custom Installer
  Builder, testing its ability to produce well formed installers. Requires the
  Seattle integration test libraries, which should be in the Python path. The
  corresponding 'seattle_gmail_info' file should be present in the directory in
  which this script is run.

  Note that the XMLRPC_PROXY_URL variable must be modified below.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib
import xmlrpclib

import integrationtestlib
import send_gmail


# The URL of the XML-RPC interface. Note the trailing slash.
XMLRPC_PROXY_URL = 'https://custombuilder.poly.edu/custom_install/xmlrpc/'

# Email addresses which should be notified in case of failure, in addition to
# the default list. For example:
#     NOTIFY_LIST = ['user@example.com', 'user2@example.com']
NOTIFY_LIST = []





# These constants will help generalize the code.
PLATFORMS = set(['linux', 'mac', 'windows'])
TGZ_PLATFORMS = set(['linux', 'mac'])
ZIP_PLATFORMS = set(['windows'])

# These values will come in handy throughout several functions, so let's make
# them globally accessible.
XMLRPC_PROXY = None
TEMP_DIR = None





def build_installers():
  return_dict = dict()


  # Build data for complex installers.
  vessels = [
    {'percentage': 60, 'owner': 'alex', 'users': ['bob']},
    {'percentage': 20, 'owner': 'carl', 'users': ['darren']},
  ]

  user_data = {
    'alex': {'public_key': '12345 54321'},
    'darren': {'public_key': '67890 09876'},
  }


  #integrationtestlib.log('Building installer for operating system \'' + os_name + '\'')

  try:
    build_results = XMLRPC_PROXY.build_installers(vessels, user_data)
  except:
    integrationtestlib.log('Failed to build installer')
    return False, None

  return True, build_results





def fetch_installer(installer_url):
  if installer_url is None:
    return False, None

  #integrationtestlib.log('Fetching installer at ' + installer_url)

  try:
    installer_filename = urllib.urlretrieve(installer_url)[0]
  except:
    integrationtestlib.log('Failed to fetch installer at ' + installer_url)
    return False, None

  return True, installer_filename





def verify_vessel_info(installer_filename, os_name):
  if installer_filename is None:
    return False

  #integrationtestlib.log('Verifying installer ' + installer_filename + ' has a vesselinfo file.')

  if os_name in ZIP_PLATFORMS:
    process = subprocess.Popen(['unzip', '-l', installer_filename], stdout=subprocess.PIPE)
  elif os_name in TGZ_PLATFORMS:
    process = subprocess.Popen(['tar', 'tzf', installer_filename], stdout=subprocess.PIPE)

  file_listing = process.communicate()[0]

  if file_listing.find('seattle/seattle_repy/vesselinfo') < 0:
    integrationtestlib.log('Installer ' + installer_filename + ' does not have a vesselinfo file.')
    return False

  return True



def decompress_installer(installer_filename, os_name):
  if installer_filename is None:
    return False

  #integrationtestlib.log('Trying to decompress ' + installer_filename)

  build_dir = tempfile.mkdtemp(dir=TEMP_DIR)
  os.chdir(build_dir)

  try:
    if os_name in ZIP_PLATFORMS:
      subprocess.check_call(['unzip', '-q', installer_filename])
    elif os_name in TGZ_PLATFORMS:
      subprocess.check_call(['tar', 'zxf', installer_filename])
  except subprocess.CalledProcessError:
    integrationtestlib.log('Installer ' + installer_filename + ' could not be decompressed.')
    return False

  return True




def run_tests():
  test_results = dict()

  integrationtestlib.log('Preparing an installer for all platforms.')
  build_success, build_results = build_installers()

  for os_name in PLATFORMS:
    integrationtestlib.log('Testing an installer for operating system \'' + os_name + '\'')

    installer_url = build_results['installers'][os_name]

    results = dict()
    results['download'], installer_filename = fetch_installer(installer_url)
    results['vessel_info'] = verify_vessel_info(installer_filename, os_name)
    results['decompress'] = decompress_installer(installer_filename, os_name)

    test_results[os_name] = results

  return test_results




def report_results(test_results):
  failures = ''

  for os_name in test_results:
    tests_failed = ''

    for test_name in test_results[os_name]:
      if not test_results[os_name][test_name]:
        tests_failed += test_name + ' '

    if tests_failed != '':
      failures += '  ' + os_name + ': ' + tests_failed + '\n'

  if failures == '':
    integrationtestlib.log('All tests successful!')
  else:
    results = 'The following tests failed:\n\n' + failures
    integrationtestlib.log(results)
    integrationtestlib.notify(results, 'Custom Installer Builder test failure')


def main():
  # Modify the global versions of these variables.
  global TEMP_DIR, XMLRPC_PROXY

  # Setup the integration test library. This must be done before changing
  # directories.
  success, explanation = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log('Failed to execute init_gmail(): ' + explanation)
    sys.exit(1)

  # Add any extra error log recipients.
  integrationtestlib.notify_list.extend(NOTIFY_LIST)

  # Establish a temporary directory to do our work in.
  TEMP_DIR = tempfile.mkdtemp()
  os.chdir(TEMP_DIR)

  # Each test can reuse this proxy.
  XMLRPC_PROXY = xmlrpclib.ServerProxy(XMLRPC_PROXY_URL)

  # The main event!
  try:
    test_results = run_tests()
    report_results(test_results)
  finally:
    # Remove the temporary directory we've been working in.
    shutil.rmtree(TEMP_DIR)


if __name__ == '__main__':
  main()
