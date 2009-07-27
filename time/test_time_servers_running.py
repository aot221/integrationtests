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

# use repy helper to bring in advertise.repy
import repyhelper
repyhelper.translate_and_import('advertise.repy')

def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)


 
  
  # verify that there are at least 8 time servers running
  servers = centralizedadvertise_lookup("time_server")
  if len(servers) < 8:
    print 'WARNING: only '+str(len(servers))+' timeservers are running!'
    
    integrationtestlib.notify('WARNING: test_time_servers_running.py FAILED, only '+str(len(servers))+' timeservers are running!')


if __name__ == '__main__':
  main()
