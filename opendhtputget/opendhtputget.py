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
import openDHTadvertise

# Armon: This is to replace using the time command with getruntime
import nonportable

# event for communicating when the lookup is done or timedout
lookup_done_event = threading.Event()



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
    notify_msg = "OpenDHT lookup failed -- lookup_timedout() fired after 30 sec."
    
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

    integrationtestlib.notify(notify_msg)
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
        
    key = random.randint(4,2**30)
    value = random.randint(4,2**30)
    ttlval = 60

    # put(key,value) with ttlval into OpenDHT
    integrationtestlib.log("calling openDHTadvertise.announce(key: " + str(key) + ", val: " + str(value) + ", ttl: " + str(ttlval) + ")")
    try:
        openDHTadvertise.announce(key,value,ttlval)
    except:
        integrationtestlib.handle_exception("openDHTadvertise.announce() failed")
        sys.exit(0)

    # a 30 second timer to email the notify_list on slow lookups
    lookup_timedout_timer = threading.Timer(30, lookup_timedout)
    # start the lookup timer
    lookup_timedout_timer.start()

    # get(key) from OpenDHT
    integrationtestlib.log("calling openDHTadvertise.lookup(key: " + str(key) + ")")
    try:
        ret_value = openDHTadvertise.lookup(key)
        # TODO: check the return value as well
        # ret_value = int(ret_value[0])
    except:
        integrationtestlib.handle_exception("openDHTadvertise.lookup() failed")
        sys.exit(0)

    lookup_timedout_timer.cancel()
    lookup_done_event.set()
    return

if __name__ == "__main__":
    main()
    
