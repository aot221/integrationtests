"""
<Program Name>
  monitor_disk.py

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu

<Usage>
  python monitor_disk.py
"""

import os
import sys
import socket
import subprocess
import send_gmail
import irc_seattlebot
import integrationtestlib


def main():


  success,explanation_str = send_gmail.init_gmail()

  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  command = "df -h | grep '/dev/sda' | awk '{print $5}'"
  command_output_fd = os.popen(command)
  
  # Get the output and get rid of the extra lines and % sign.
  disk_use_percent = int(command_output_fd.read().split()[0][:-1])

  hostname = socket.gethostname() + ".cs.washington.edu"
  subject = "High disk usage"

  if disk_use_percent > 95:
    message = "CRITICAL: Very High Disk Usage on %s: %s percent used" % ( hostname, disk_use_percent)
    integrationtestlib.notify(message, subject)
    irc_seattlebot.send_msg(message)

  elif disk_use_percent > 90:
    message = "WARNING: High disk usage on %s: %s percent used" % ( hostname, disk_use_percent)
    integrationtestlib.notify(message, subject)

  





if __name__ == "__main__":
  main()
