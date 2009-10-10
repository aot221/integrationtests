#!/usr/bin/python
"""
<Program Name>
  downloadandinstallseattle.py

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

  - GMAIL_USER and GMAIL_PWD environment variables: the username and
    password of the gmail user who will be sending the email to the
    emails in the notify_list (see crontab line below).

  This script takes no arguments. A typical use of this script is to
  have it run periodically using something like the following crontab line:
  7 * * * *  export GMAIL_USER='username' && export GMAIL_PWD='password' && /usr/bin/python /home/seattle/downloadandinstallseattle/downloadandinstallseattle.py > /home/seattle/cron_log.downloadandinstallseattle
"""

import time
import os
import socket
import sys
import traceback

import send_gmail
import integrationtestlib

# path prefix where we will download and install seattle
prefix=os.getcwd()

# the url from where we will fetch a linux version of seattle
seattle_linux_url = "https://seattlegeni.cs.washington.edu/geni/download/seattle_install_tester/seattle_linux.tgz"

# public key we will check for after seattle registers with geni
# onepercent.publickey:
# onepercent_publickey_e = 60468416553866380677116390576156076729024198623214398075105135521876532012409126881929651482747468329767098025048318042065154275278061294675474785736741621552566507350888927966579854246852107176753219560487968433237288004466682136195693392768043076334227134087671699044294833943543211464731460317203206091697L

# onepercent2.publickey:
#onepercent_publickey_e = 11374924881397627694657891503972818975279141290591879258944253588899600389096760006002101031499188547300330800546193710201543484693030070856785048737553629L

# onepercent_manyevents.publickey:
onepercent_publickey_e = 100410155996328658394016174672712730146493471136460054943977610055010406541029967456210961113332433120911220994866027327246525018914945308813146095094266583446333536819644021403563644749883453501917642715769556118483161623360060413817439150957963107024505503830466865934362815594494856415719036027721190604347L



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
    integrationtestlib.log("uninstalling")
    os.system("cd " + prefix + "/seattle/ && chmod +x ./uninstall.sh && ./uninstall.sh");

    # remove all traces
    integrationtestlib.log("removing all files")
    os.system("rm -Rf " + prefix + "/seattle/");
    os.system("rm -Rf " + prefix + "/seattle_linux.tgz")
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
    integrationtestlib.log("downloading distro for seattle_install_tester...")
    os.system("wget --no-check-certificate " + seattle_linux_url)
    integrationtestlib.log("unpacking...")
    os.system("tar -xzvf " + prefix + "/seattle_linux.tgz")
    integrationtestlib.log("installing...")
    os.system("cd " + prefix + "/seattle/ && ./install.sh")
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

    # download and install Seattle
    download_and_install()

    # sleep for a while, giving GENI time to process this new node
    integrationtestlib.log("sleeping for 30 minutes...")
    time.sleep(1800)
    
    # retrieve the vesseldict from installed seattle
    integrationtestlib.log("retrieving vesseldict from installed Seattle")
    dict = {}
    try:
        f=open(prefix + "/seattle/seattle_repy/vesseldict", "r")
        lines = f.readlines()
        f.close()
        dict = eval(lines[0])
    except:
        integrationtestlib.handle_exception("failed to open/read/eval vesseldict file", "seattle downloadandinstall failed!")
        # uninstall Seattle and remove its dir
        uninstall_remove()
        sys.exit(0)

    # check if the vesseldict conforms to expectations
    integrationtestlib.log("checking for onepercent pubkey in vessels..")
    passed = False
    try:
        for vname, vdata in dict.items():
            for k in vdata['userkeys']:
                if k['e'] == onepercent_publickey_e:
                    integrationtestlib.log("passed")
                    passed = True
                    break
            if passed:
                break
    except e:
        integrationtestlib.handle_exception("failed in checking for onepercent key\n\nvesseldict is: " + str(dict), "seattle downloadandinstall failed!")
        # uninstall Seattle and remove its dir
        uninstall_remove()
        sys.exit(0)

    # if vesseldict not as expected, notify some people
    if not passed:
        text = "check for onepercent key:\n" + str(onepercent_publickey_e) + "..\n\nfailed\n\nvesseldict is: " + str(dict)
        integrationtestlib.log(text)
        integrationtestlib.notify(text, "seattle downloadandinstall failed!")
    
    # uninstall Seattle and remove its dir
    uninstall_remove()
    return


if __name__ == "__main__":
    main()
    
