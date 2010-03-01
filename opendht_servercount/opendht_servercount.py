"""
<Program Name>
  opendht_servercount.py

<Started>
  February 28th 2010

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Usage>
  This script takes no argument. Just make sure all the required
  files are in the directory and run the program and redirect its
  output to some log file.

  Usually a crontab for this program would be set up, so this program
  runs periodically. Once a day should be enough for this program.

  Example:
  0 3 * * * /usr/bin/python /home/itegrationtests/opendht_servercount.py >> /home/integrationtests/cron_log.opendht_servercount
"""

import send_gmail
import integrationtestlib
import repyhelper
import sys

repyhelper.translate_and_import("openDHTadvertise.repy")

# The number of servers that must be up at all times.
min_num_servers = 50


def check_opendht_servers():
  """
  <Purpose>
    Checks to see how many servers are up for the opendht advertisement.
    If the number of server is less then 100 then an email notification
    is sent to the seattle developers.

  <Argument>
    None

  <Exception>
    None

  <Side_Effects>
    None

  <Returns>
    None
  """

  notify_message = "There aren't enough opendht servers up and running currently."
  subject = "opendht_servercount test failed."

  try:
    # Retrieve the list of servers for opendht
    opendht_server_list = openDHTadvertise_get_proxy_list(maxnumberofattempts = 150)
  except:
    # An exception is raised if there are no servers up and running for opendht by
    # openDHTadvertise_get_proxy_list().
    integrationtestlib.handle_exception("There are no servers up for opendht!", subject)

  integrationtestlib.log("Retrieved the list of opendht servers up and running.")
  integrationtestlib.log("There are " + str(len(opendht_server_list)) + " servers up and running for opendht advertisement.")

  # Check to see if there are less then 100 servrs up and running.
  # If there are less then 100 servers running then notify the seattle
  # developers about it.
  if len(opendht_server_list) < min_num_servers:
    subject += " There are only " + str(len(opendht_server_list)) + " servers up and running for opendht advertisement."
    integrationtestlib.notify(notify_message, subject)




def main():
  """
  <Purpose>
    Initialize the gmail info that is needed to send email notifications.
    Call the function to check if enough opendht servers are running.

  <Arguments>
    None
  
  <Exceptions>
    None

  <Side_Effects>
    None

  <Return>
    None
  """

  # Setup the gmail user/password to use when sending email.
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  # Run the test to see how many servers are up.
  check_opendht_servers() 

 


if __name__ == "__main__":
    main()
