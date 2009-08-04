"""
<Program Name>
  test_nat_servers_running.py

<Started>
  Jul 26, 2009

<Author>
  Eric Kimbrel

<Purpose>
  Send out emails if fewer than 10 nat servers are running
  or we can not get a response from nat_check_bi_directional()
"""

import sys
import send_gmail
import integrationtestlib

# use repy helper to bring in advertise.repy
import repyhelper
repyhelper.translate_and_import('NATLayer_rpc.repy')

def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  #add Eric Kimbrel to the email notify list
  integrationtestlib.notify_list.append("lekimbrel@gmail.com")
  
  # PART 1 verify that there are at least 10 nat forwarders running
  integrationtestlib.log("Looking up nat forwarders")  
  try:
    nodes = nat_forwarder_list_lookup()
  except:
    nodes = [] #make sure we fail if there was an excpetion

  if len(nodes) < 10:
    integrationtestlib.log('WARNING: only '+str(len(nodes))+' forwarders are running!')
    
    integrationtestlib.notify('WARNING: test_nat_servers_running.py FAILED, only '+str(len(servers))+' nat forwarders are running!')




  # PART 2 check that nat forwarders are responsive
  integrationtestlib.log("Checking that we can talk to a nat forwarder")  
  try:
    response = nat_check_bi_directional(getmyip(),55000) 
  except:
    response = None

  if response != True and response != False:
    integrationtestlib.log('WARNING: nat forwarders appear un-responsive')

    integrationtestlib.notify('WARNING: test_nat_servers_running.py FAILED, nat forwarders did not respond')
    
  integrationtestlib.log("Finished running nat_tests")
  print "------------------------------------------------------------"


if __name__ == '__main__':
  main()
