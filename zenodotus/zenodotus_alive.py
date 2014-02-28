"""
<Filename>
  zenodotus_alive.py

<Purpose>
  This is an integration test script that will look up zenodotus via
  DNS to ensure that it points to blackbox.

"""
import integrationtestlib
import send_gmail
import os
import sys

def main():
  # Initialize the gmail setup.
  success, explanation_str = send_gmail.init_gmail()

  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  print "Beginning query."
  success = True

  try:
    # Query zenodotus
    for line in os.popen('dig @8.8.8.8 zenodotus.poly.edu', 'r').readlines():
      # Can't do direct comparison between dig's output and hardcoded string
      # TTL value changes on each call.  Instead, check if any of the lines
      # contain the entry for blackbox.
      if 'zenodotus.poly.edu.' in line.split() and '128.238.63.50' in line.split():
        break
    else:
      print "Zenodotus failed to respond properly!"
      # Query is invalid!
      success = False
      integrationtestlib.notify("Error: Zenodotus has failed to correctly respond; the machine has likely been rebooted. Please restart the zenodotus server on zenodotus@blackbox. This report will be re-sent hourly while the problem persists.", "Cron: Zenodotus failure")
  except Exception, e:
    print "Unknown error!"
    print str(e)
    success = False
    integrationtestlib.notify("Error: Zenodotus seems to be down! Error data: " + str(e), "Cron: Zenodotus failure")

  if success:
    print "Query was successful."

if __name__ == "__main__":
  main()
