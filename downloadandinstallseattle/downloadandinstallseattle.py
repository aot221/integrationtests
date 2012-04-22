#!/usr/bin/python
"""
<Program Name>
  downloadandinstallseattle.py

<Started>
  December 6, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh
  
  monzum@cs.washington.edu
  Monzur Muhammad

<Purpose>
  Download, install and check the resulting Seattle installation for
  correct state (onepercent state).

<Usage>
  Modify the following global var params to have this script functional:
  - prefix, where this script will execute

  - seattle_linux_url, the url of the seattle distro to download,
    install, check

  - twopercent_publickey, the twopercent node state 

  - integrationtestlib.notify_list, a list of strings with emails denoting who will be
    emailed when something goes wrong

  This script takes no arguments. A typical use of this script is to
  have it run periodically using something like the following crontab line:
  7 * * * * /usr/bin/python /home/seattle/downloadandinstallseattle/downloadandinstallseattle.py > /home/seattle/cron_log.downloadandinstallseattle
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
#onepercent_publickey_e = 10041015599632865839401617467271273014649347113646005494397761005501040654102996745621096111333243312091122099486602732724652501891494530881314609509426658344633353681964402140356364474988345350

# onepercent_manyevents.publickey:
#onepercent_publickey_e = 100410155996328658394016174672712730146493471136460054943977610055010406541029967456210961113332433120911220994866027327246525018914945308813146095094266583446333536819644021403563644749883453501917642715769556118483161623360060413817439150957963107024505503830466865934362815594494856415719036027721190604347L
twopercent_publickey = {'e': 65537L, 'n': 104283973845452278473567059872058302181099306478946860695753925866960062455387034090984928649172368336895511957180608166358198358557811956058533160134655085887217281584650941950088412008071410745320003819243027473383767411456759901168591653498109515401427898370664550473756850087580169500147037740069933812133L}

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

    if(os.path.isfile(prefix+"/seattle_linux.tgz")):
        os.remove(prefix+"/seattle_linux.tgz")

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

    # sleep for a while, giving Clearinghouse time to process this new node
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
    integrationtestlib.log("checking for twopercent pubkey in vessels..")
    passed = False
    try:
        for vname, vdata in dict.items():
            for k in vdata['userkeys']:
                if k == twopercent_publickey:
                    integrationtestlib.log("passed")
                    passed = True
                    break
            if passed:
                break
    except e:
        integrationtestlib.handle_exception("failed in checking for twopercent key\n\nvesseldict is: " + str(dict), "seattle downloadandinstall failed!")
        # uninstall Seattle and remove its dir
        uninstall_remove()
        sys.exit(0)

    # if vesseldict not as expected, notify some people
    if not passed:
        text = "check for twopercent key:\n" + str(twopercent_publickey) + "..\n\nfailed\n\nvesseldict is: " + str(dict)
        integrationtestlib.log(text)
        integrationtestlib.notify(text, "seattle downloadandinstall failed!")

    # uninstall Seattle and remove its dir
    uninstall_remove()
    return



if __name__ == "__main__":
    main()
    
