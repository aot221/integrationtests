#!/usr/bin/python
"""
<Program Name>
  opendhtputget.py

<Started>
  December 6, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Attempt to put a (k,v) into OpenDHT and then get it back. On error
  send an email to some folks.

<Usage>
  Modify the following global var params to have this script functional:
  - notify_list, a list of strings with emails denoting who will be
    emailed when something goes wrong

  This script takes no arguments. A typical use of this script is to
  have it run periodically using something like the following crontab line:
  7 * * * * /usr/bin/python /home/seattle/opendhtputget.py > /home/seattle/cron_log.opendhtputget
"""

import time
import os
import socket
import sys
import traceback
import threading
import random

import send_gmail
import integrationtestlib
import repyhelper

repyhelper.translate_and_import("/home/monzum/opendhtputget_new/openDHTadvertise.repy")

# Armon: This is to replace using the time command with getruntime
import nonportable

# event for communicating when the lookup is done or timedout
lookup_done_event = threading.Event()

lookup_timeout_fired = 0

def lookup_timedout():
    """
    <Purpose>
       Waits for lookup_done_event and notifies the folks on the
       notify_list (global var) of the lookup timeout.

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        Sends an email to the notify_list folks

    <Returns>
        None.
    """
    integrationtestlib.log("in lookup_timedout()")
    notify_msg = "OpenDHT lookup failed -- lookup_timedout() fired after 60 seconds."
    subject = "opendht with repy test failed"    

    global lookup_timeout_fired

    lookup_timeout_fired += 1

    # wait for the event to be set, timeout after 30 minutes
    wait_time = 1800
    tstamp_before_wait = nonportable.getruntime()
    lookup_done_event.wait(wait_time)
    tstamp_after_wait = nonportable.getruntime()

    t_waited = tstamp_after_wait - tstamp_before_wait
    if abs(wait_time - t_waited) < 5:
        notify_msg += " And lookup stalled for over 30 minutes (max timeout value)."
    else:
        notify_msg += " And lookup stalled for " + str(t_waited) + " seconds"

    if lookup_timeout_fired >= 5:
      integrationtestlib.notify(notify_msg,subject )
    return


def main():
    """
    <Purpose>
        Program's main.

    <Arguments>
        None.

    <Exceptions>
        All exceptions are caught.

    <Side Effects>
        None.

    <Returns>
        None.
    """
    # setup the gmail user/password to use when sending email
    success,explanation_str = send_gmail.init_gmail()
    if not success:
      integrationtestlib.log(explanation_str)
      sys.exit(0)


    integrationtestlib.notify_list.append("cemeyer@u.washington.edu")

    ttlval = 60
    subject = "opendht with repy test failed"

    fail_count = 0
    message = "openDHTadvertise_lookup() or openDHTadvertise_announce failed 5 times."

    for i in range(5):
      key = random.randint(4,2**30)
      value = random.randint(4,2**30)

      # put(key,value) with ttlval into OpenDHT
      integrationtestlib.log("calling openDHTadvertise_announce(key: " + str(key) + ", val: " + str(value) + ", ttl: " + str(ttlval) + ")")
      try:
        openDHTadvertise_announce(key, value, ttlval, proxiestocheck = 10)
      except:
        fail_count += 1
        message = message + "\nAnouncing with key: " + str(key) + ", value: " + str(value) + ", ttlval: " + str(ttlval)
        if fail_count >= 5:
          integrationtestlib.handle_exception(message, subject)
          sys.exit(0)
        continue


      # a 60 second timer to email the notify_list on slow lookups
      lookup_timedout_timer = threading.Timer(60, lookup_timedout)
      # start the lookup timer
      lookup_timedout_timer.start()

      # get(key) from OpenDHT
      integrationtestlib.log("calling openDHTadvertise_lookup(key: " + str(key) + ")")
      try:
        ret_value = openDHTadvertise_lookup(key, proxiestocheck = 10)
        # TODO: check the return value as well
        # ret_value = int(ret_value[0])
      except:
        fail_count += 1
        message = message + "Looking up with key: " + str(key)
  
        if fail_count >= 5:
          integrationtestlib.handle_exception(message, subject)
          sys.exit(0)

      lookup_timedout_timer.cancel()
      lookup_done_event.set()

    return

if __name__ == "__main__":
    main()
    
