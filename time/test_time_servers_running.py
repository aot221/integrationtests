"""
<Program Name>
  test_time_servers_running.py

<Started>
  Jul 26, 2009

<Author>
  Eric Kimbrel

<Purpose>
  Send out emails if fewer than 8 timeservers are running
"""

import sys
import send_gmail
import integrationtestlib
import traceback

# use repy helper to bring in advertise.repy
import repyhelper
repyhelper.translate_and_import('advertise.repy')

def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  #add Eric Kimbrel to the email notify list
  integrationtestlib.notify_list.append("lekimbrel@gmail.com")
  
  try:
    integrationtestlib.log("Looking up time_servers")

    # verify that there are at least 8 time servers running
    servers = advertise_lookup("time_server")
    if len(servers) < 8:
      integrationtestlib.log('WARNING: only '+str(len(servers))+' timeservers are running!')
    
      integrationtestlib.notify('WARNING: test_time_servers_running.py FAILED, only '+str(len(servers))+' timeservers are running!', "test_time_servers_running test failed")
  
    integrationtestlib.log("Finished looking up test servers... Test Passed")
    print "........................................................\n"
  except:
    integrationtestlib.notify("Test failed for an unknown reason:\n" +
      traceback.format_exc(), "test_time_servers_running test failed")

if __name__ == '__main__':
  main()
