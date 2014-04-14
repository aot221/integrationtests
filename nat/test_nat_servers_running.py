"""
<Program Name>
  test_nat_servers_running.py

<Started>
  Jul 26, 2009

<Author>
  Eric Kimbrel

<Purpose>
  Send out emails if fewer than 10 nat servers are running

"""

import send_gmail
import integrationtestlib

from repyportability import *
add_dy_support(locals())

advertise = dy_import_module('advertise.repy')
nat_forwarder_common_lib = dy_import_module('nat_forwarder_common_lib.repy')


# These are the keys we'll be monitoring
nat_forwarder_keys = nat_forwarder_common_lib.NAT_FORWARDER_KEY
NAT_TEST_FAIL_NOTICE = "test_nat_servers_running FAILED"

def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  # PART 1 verify that there are at least 10 nat forwarders running on
  # each key

  notify_str = ''
  for nat_forwarder_key in nat_forwarder_keys:
    integrationtestlib.log("Looking up nat forwarders for " + repr(nat_forwarder_key))
    nat_forwarders = []
    try:
      nat_forwarders = advertise.advertise_lookup(nat_forwarder_key)
    except Exception, e:
      integrationtestlib.handle_exception("Got exception when looking up nat forwarders", NAT_TEST_FAIL_NOTICE)
      return

    if len(nat_forwarders) < 10:
      notify_str += ('WARNING: only '+ str(len(nat_forwarders))
        + ' nat forwarders are advertising under the key: '
        + repr(nat_forwarder_key) + '\n'
        + "Advertising forwarders: " + str(nat_forwarders) + '\n')

  if notify_str:
    integrationtestlib.log(notify_str)
    integrationtestlib.notify(notify_str, NAT_TEST_FAIL_NOTICE)

  # # PART 2 check that nat forwarders are responsive
  # TODO: Change this to use Affixes on repyV2
  # integrationtestlib.log("Checking that we can talk to a nat forwarder")
  # try:
  #   response = nat_check_bi_directional(getmyip(),random.randint(20000,62000))
  # except Exception, e:
  #   notify_str += 'WARNING: could not a get a response from nat forwarders: '+str(e)

  #   integrationtestlib.log('WARNING: could not get a response from nat forwarders '+str(e))

  integrationtestlib.log("Finished running nat_tests")
  print "------------------------------------------------------------"


if __name__ == '__main__':
  main()
