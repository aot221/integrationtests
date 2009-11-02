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
import random


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
  
  notify_str =''


  # PART 1 verify that there are at least 10 nat forwarders running
  integrationtestlib.log("Looking up nat forwarders")  
  try:
    nodes = nat_forwarder_list_lookup()
    total_nodes = advertise_lookup('NATFORWARDERRUNNING')
  except:
    nodes = [] #make sure we fail if there was an excpetion

  if len(nodes) < 10:
    integrationtestlib.log('WARNING: only '+str(len(nodes))+' forwarders are avaiable')
    integrationtestlib.log('WARNING: only '+str(len(total_nodes))+' forwarders are running')
    
    notify_str += 'WARNING: test_nat_servers_running.py FAILED, only '+str(len(nodes))+' nat forwarders are avaiable!,  '+str(len(total_nodes))+' are running.'


  # PART 2 check that nat forwarders are responsive
  integrationtestlib.log("Checking that we can talk to a nat forwarder")  
  try:
    response = nat_check_bi_directional(getmyip(),random.randint(20000,62000))
  except Exception, e:
    notify_str += 'WARNING: could not a get a response from nat forwarders: '+str(e)
  
    integrationtestlib.log('WARNING: could not get a response from nat forwarders '+str(e))

  if notify_str != '':
    integrationtestlib.notify(notify_str,'nat test fail notice')
    
  integrationtestlib.log("Finished running nat_tests")
  print "------------------------------------------------------------"


if __name__ == '__main__':
  main()
