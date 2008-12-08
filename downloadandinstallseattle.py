#!/usr/bin/python
"""
<Program Name>
  genidb.py

<Started>
  December 6, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Download, install and check the resulting Seattle installation for
  correct state (onepercent state).

<Usage>
  Modify the following global var params to have this script functional:
  - prefix, where this script will execute

  - seattle_linux_url, the url of the seattle distro to download,
    install, check

  - onepercent_publickey_e, the onepercent node state e part of the
    public key (what's checked after the install)

  - notify_list, a list of strings with emails denoting who will be
    emailed when something goes wrong

  - gmail_user, email_pwd, the username and password of the gmail user
    who will be sending the email to the emails in the notify_list

  This script takes no arguments. A typical use of this script is to
  have it run periodically via, using something like the following
  crontab line:
  7 * * * * /usr/bin/python /home/seattle/download_and_install_seattle.py > /home/seattle/cron_log.txt
"""

import time
import os
import socket
import sys
import traceback

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

prefix="/home/seattle"
seattle_linux_url = "https://seattle.cs.washington.edu/geni/download/seattle_install_tester/linux"
onepercent_publickey_e = 60468416553866380677116390576156076729024198623214398075105135521876532012409126881929651482747468329767098025048318042065154275278061294675474785736741621552566507350888927966579854246852107176753219560487968433237288004466682136195693392768043076334227134087671699044294833943543211464731460317203206091697L
notify_list = ["ivan@cs.washington.edu", "justinc@cs.washington.edu"]

try:
    gmail_user = os.environ['GMAIL_USER']
except:
    print "Failed to retrieve GMAIL_USER from shell environ"
    sys.exit(0)

try:
    gmail_pwd = os.environ['GMAIL_PWD']
except:
    print "Failed to retrieve GMAIL_PWD from shell environ"
    sys.exit(0)

def mail(to, subject, text, attach):
    """
    <Purpose>
        Function to send an email to 'to' with subject 'subject' with
        text 'test' and attachment filename 'attach'

    <Arguments>
        to, who to send the email to, an email address string
        subject, the string subject line of the email
        text, the string text body of the email
        attach, the filename to attach to the message

    <Exceptions>
        Not sure?

    <Side Effects>
        Sends an email through gmail to a recipient.

    <Returns>
        None.
    """
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    if attach != "":
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()
    return

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

def uninstall_remove():
    """
    <Purpose>
       Uninstalls a Seattle installation and removes the Seattle directory

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        Uninstalls Seattle and removes its directory

    <Returns>
        None.
    """
    # uninstall
    log("uninstalling")
    os.system("cd " + prefix + "/seattle_repy/ && chmod +x ./uninstall.sh && ./uninstall.sh");

    # remove all traces
    log("removing all files")
    os.system("rm -Rf " + prefix + "/seattle_repy/");
    os.system("rm -Rf " + prefix + "/seattle_linux.tgz")
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
        mail(emailaddr, subj, text, "")
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

    # uninstall Seattle and remove its dir
    uninstall_remove()
    return


def download_and_install():
    """
    <Purpose>
        Downloads and installs Seattle

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        Downloads a .tgz file. Unpacks it and installs Seattle (this modifies the user's crontab).

    <Returns>
        None.
    """
    log("downloading distro for seattle_install_tester...")
    os.system("wget --no-check-certificate " + seattle_linux_url)
    log("unpacking...")
    os.system("tar -xzvf " + prefix + "/seattle_linux.tgz")
    log("installing...")
    os.system("cd " + prefix + "/seattle_repy/ && ./install.sh")
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
    # download and install Seattle
    download_and_install()

    # sleep for a while, giving GENI time to process this new node
    log("sleeping for 30 minutes...")
    time.sleep(1500)
    
    # retrieve the vesseldict from installed seattle
    log("retrieving vesseldict from installed Seattle")
    dict = {}
    try:
        f=open(prefix + "/seattle_repy/vesseldict", "r")
        lines = f.readlines()
        f.close()
        dict = eval(lines[0])
    except:
        handle_exception("failed to open/read/eval vesseldict file")
        sys.exit(0)

    # check if the vesseldict conforms to expectations
    log("checking for onepercent pubkey in vessels..")
    passed = False
    try:
        for vname, vdata in dict.items():
            for k in vdata['userkeys']:
                if k['e'] == onepercent_publickey_e:
                    log("passed")
                    passed = True
                    break
            if passed:
                break
    except e:
        handle_exception("failed in checking for onepercent key\n\nvesseldict is: " + str(dict))
        sys.exit(0)

    # if vesseldict not as expected, notify some people
    if not passed:
        text = "check for onepercent key:\n" + str(onepercent_publickey_e) + "..\n\nfailed\n\nvesseldict is: " + str(dict)
        log(text)
        notify(text)
    
    # uninstall Seattle and remove its dir
    uninstall_remove()
    return


if __name__ == "__main__":
    main()
    
