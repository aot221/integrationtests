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

  - GMAIL_USER and GMAIL_PWD environment variables: the username and
    password of the gmail user who will be sending the email to the
    emails in the notify_list (see crontab line below).

  This script takes no arguments. A typical use of this script is to
  have it run periodically using something like the following crontab line:
  7 * * * *  export GMAIL_USER='..' && export GMAIL_PWD='..' && /usr/bin/python /home/seattle/opendhtputget.py > /home/seattle/cron_log.opendhtpuget
"""

import time
import os
import socket
import sys
import traceback
import threading
import random

import send_gmail
import openDHTadvertise

# list of people to notify by email on failure
notify_list = ["ivan@cs.washington.edu", "justinc@cs.washington.edu"]

# event for communicating when the lookup is done or timedout
lookup_done_event = threading.Event()


def log(msg):
    """
    <Purpose>
       Prints a particularly formatted log msg to stdout

    <Arguments>
        msg, the text to print out

    <Exceptions>
        None.

    <Side Effects>
        Prints a line to stdout.

    <Returns>
        None.
    """
    print time.ctime() + " : " + msg
    return

def notify(text):
    """
    <Purpose>
       Send email with message body text to the members of the notify_list

    <Arguments>
        text, the text of the email message body to be generated

    <Exceptions>
        None.

    <Side Effects>
        Sends email.

    <Returns>
        None.
    """
    try:
        hostname = socket.gethostname()
    except:
        hostname = "unknown host"
    else:
        try:
            hostname = socket.gethostbyname_ex(hostname)[0]
        except:
            pass
    subj = "seattle test failed @ " + hostname + " : " + sys.argv[0]
    for emailaddr in notify_list:
        log("notifying " + emailaddr)
        send_gmail.send_gmail(emailaddr, subj, text, "")
    return


def handle_exception(text):
    """
    <Purpose>
       Handles an exception with descriptive text.

    <Arguments>
        text, descriptive text to go along with a generated exception

    <Exceptions>
        None.

    <Side Effects>
        Logs the exception. Notifies people via email. Uninstalls Seattle and remove the Seattel dir.

    <Returns>
        None.
    """
    # log the exception
    text = "Exception: " + text + "\n"
    log(text)
    text = "[" + time.ctime() + "]" + text
    print '-'*60
    traceback.print_exc(file=sys.stdout)
    print '-'*60

    # build the exception traceback string
    error_type, error_value, trbk = sys.exc_info()
    # use traceback max recursion depth of 6
    tb_list = traceback.format_tb(trbk, 6)
    exception_traceback_str = "Error: %s \nDescription: %s \nTraceback:" % (error_type.__name__, error_value)
    for i in tb_list:
        exception_traceback_str += "\n" + i
    
    # notify folks via email with the traceback of the exception
    notify(text + exception_traceback_str)
    return

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
    log("in lookup_timedout()")
    notify_msg = "OpenDHT lookup failed -- lookup_timedout() fired after 30 sec."
    
    # wait for the event to be set, timeout after 30 minutes
    wait_time = 1800
    tstamp_before_wait = time.time()
    lookup_done_event.wait(wait_time)
    tstamp_after_wait = time.time()

    t_waited = tstamp_after_wait - tstamp_before_wait
    if abs(wait_time - t_waited) < 5:
        notify_msg += " And lookup stalled for over 30 minutes (max timeout value)."
    else:
        notify_msg += " And lookup stalled for " + str(t_waited) + " seconds"

    notify(notify_msg)
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
        log(explanation_str)
        sys.exit(0)
        
    key = random.randint(4,2**30)
    value = random.randint(4,2**30)
    ttlval = 60

    # put(key,value) with ttlval into OpenDHT
    log("calling openDHTadvertise.announce(key: " + str(key) + ", val: " + str(value) + ", ttl: " + str(ttlval) + ")")
    try:
        openDHTadvertise.announce(key,value,ttlval)
    except:
        handle_exception("openDHTadvertise.announce() failed")
        sys.exit(0)

    # a 30 second timer to email the notify_list on slow lookups
    lookup_timedout_timer = threading.Timer(30, lookup_timedout)
    # start the lookup timer
    lookup_timedout_timer.start()

    # get(key) from OpenDHT
    log("calling openDHTadvertise.lookup(key: " + str(key) + ")")
    try:
        ret_value = openDHTadvertise.lookup(key)
        # TODO: check the return value as well
        # ret_value = int(ret_value[0])
    except:
        handle_exception("openDHTadvertise.lookup() failed")
        sys.exit(0)

    lookup_timedout_timer.cancel()
    lookup_done_event.set()
    return

if __name__ == "__main__":
    main()
    
