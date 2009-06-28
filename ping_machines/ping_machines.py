"""
<Program Name>
  ping_machines.py

<Started>
  June 23, 2009

<Author>
  Monzur Muhammad
  monzum@u.washington.edu
  
<Purpose>
  ping_machines.py should run once an hour on a crontab. Every machine that is involved in the Seattle project
  is pinged to make sure that the machine is up and running. If any of the machine cannot be pinged, an email
  is sent to the system admins and also a message is sent on the irc. If all the pings were successful then
  a message is sent on the irc, once a day.
  
<Usage>
  This file should run on a crontab such as this:
  
  25 * * * * export GMAIL_USER='seattle.devel@gmail.com' && export GMAIL_PWD='repyrepy' && /usr/bin/python
  /home/integrationtester/cron_tests/ping_machines/ping_machines.py >> /home/integrationtester/cron_logs/cron_log.ping_machines 2>&1
"""


import os
import time
import sys
import socket
import subprocess
import send_gmail
import irc_seattlebot
import re
from threading import Thread


#list of critical machines that should be always up and running 
machine_list = ["seattle.cs.washington.edu", "seattlegeni.cs.washington.edu", "blackbox.cs.washington.edu", "testbed-xp2.cs.washington.edu", "testbed-freebsd.cs.washington.edu", "testbed-opensuse.cs.washington.edu", "testbed-mac.cs.washington.edu"]

# the people to notify on failure/if anything goes wrong
notify_list = ["ivan@cs.washington.edu", "justinc@cs.washington.edu", "monzum@u.washington.edu"]


#Exception if an unknown hostname is pinged
class MachineDoesNotExist(Exception):
  pass 


class ping(Thread):
  """
  <Purpose>
    This class spawns a new thread, which pings a machine to check
    if it is running and can be pinged.

  <Exception>
    None

  <Side Effect>
    None

  <Usage>
    ping(<machine_name>)
  """
 
  def __init__ (self, ipaddr, result_queue, pingcount=5):
    Thread.__init__(self)
    self.ipaddr=ipaddr
    self.pingcount = pingcount
    self.result_queue = result_queue

  def run(self):
    """
    <Purpose>
      The thread function that actually pings the machines

    <Arguments>
      ipaddr - the ip address or the hostname of the machine
      pingcount - number of times the machine should be pinged
        by default the machines are pinged 5 times.

    <Exception>
      raises MachineDoesNotExist exception if user is attempting to ping
      an unknown host.
 
    <Side Effect>
      prints out a form of the ping result
    """

    try:
      socket.gethostbyname(self.ipaddr)
    except:
      raise MachineDoesNotExist, "The hostname/ipaddr "+self.ipaddr+" does not exist"

    #pings the machine and gets the result line back  
    command = ("ping -q -c"+str(self.pingcount)+"  "+self.ipaddr, "r")
    pingresult = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout
    
    #stay in a while loop while the ping result isn't ready
    while True:
      ping_line = pingresult.readline()
 
      #break when the ping is over
      if not ping_line:
        break

      packets_received=re.findall(r"(\d) received", ping_line)
      
      if packets_received:
        packets_received = int(packets_received[0])*100/self.pingcount
        result= "Pinging "+str(self.ipaddr)+": packets received "+str(packets_received)+"%"
        
        print result

        if packets_received == 0:
          self.result_queue.append((False,result))
        else:
          self.result_queue.append((True,result)) 




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
  subj = "critical seattle machines down @ " + hostname + " : " + sys.argv[0]
  
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

  # uninstall Seattle and remove its dir
  uninstall_remove()
  return



def main():
  """
  <Purpose>
    Ping all the machines to see if they are up

  <Exceptions>
    none

  <Side Effects>
    Prints the ping result

  <Returns>
    None.
  """

  # setup the gmail user/password to use when sending email
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    log(explanation_str)
    sys.exit(0)

  print time.ctime() + " : pinging critical machines"

  #list of machines thats getting pinged
  pinglist = []

  #list that contains all the ping results
  result_queue = []  

  #create a thread for each machine and ping them
  for host in machine_list:
    current_machine = ping(str(host), result_queue)
    pinglist.append(current_machine)
    current_machine.start()

  #join all the threads
  for ping_host in pinglist:
    ping_host.join()

  #variable that keeps track if any machines are down  
  ALL_MACHINES_RUNNING = True
  error_message="WARNING: Seattle machines are down! Seattle developers please check on the machines.\n"
  error_message+="Displaying ping result:\n"

  #check to see if all the results were successful
  #on failures notify the admins and send a message to the irc
  for (success, result) in result_queue:
    if not success:
      ALL_MACHINES_RUNNING = False
      error_message += result+"\n"

  #if all machines were pinged successfully, notify on irc if option -m was used to run ping_machines.py
  if ALL_MACHINES_RUNNING:
    if sys.argv[1] == '-m':
      irc_seattlebot.send_msg("The machines: "+str(machine_list)+" were pinged successfully")

  else:
    handle_exception(error_message)
    irc_seattlebot.send_msg(error_message) 

    
  print time.ctime() + " : Done pinging all machiens."
  print "--------------------------------------------"

if __name__ == "__main__":
  main()     
         
 
