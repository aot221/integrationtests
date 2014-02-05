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
import integrationtestlib
import re
from threading import Thread


#list of critical machines that should be always up and running 
machine_list = ["seattle.poly.edu", "seattleclearinghouse.poly.edu", "blackbox.poly.edu", "betaseattleclearinghouse.poly.edu", "custombuilder.poly.edu"]



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
      self.result_queue.append((False, "The machine/ipaddr: "+self.ipaddr+" does not exist:"))
      raise MachineDoesNotExist, "The hostname/ipaddr "+self.ipaddr+" does not exist"
      
    #pings the machine and gets the result line back  
    command = ("ping -q -c"+str(self.pingcount)+"  "+self.ipaddr, "r")
    pingresult, pingerror = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()

    #splits up the result in order to analyze the result
    pingresult_formatted=pingresult.split('\n')

    #Go through the result and pick out the right line to analyze
    for ping_line in pingresult_formatted:

      packets_received=re.findall(r"(\d) received", ping_line)

      if packets_received:
        packets_received = int(packets_received[0])*100/self.pingcount
        result= "Pinging "+str(self.ipaddr)+": packets received "+str(packets_received)+"%"
        
        integrationtestlib.log(result)

        if packets_received == 0:
          self.result_queue.append((False,result))
        else:
          self.result_queue.append((True,result)) 



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
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  integrationtestlib.log("pinging critical machines")

  #list of machines thats getting pinged
  pinglist = []

  #list that contains all the ping results
  result_queue = []  

  #create a thread for each machine and ping them
  for host in machine_list:
    ping_current_machine = ping(str(host), result_queue)
    pinglist.append(ping_current_machine)
    ping_current_machine.start()

  #join all the threads
  for ping_host in pinglist:
    ping_host.join()

  #variable that keeps track if any machines are down  
  ALL_MACHINES_RUNNING = True
  error_message="WARNING: Seattle machines are down! Seattle developers please check on the machines.\n"
  error_message+="Displaying ping result:\n"

  #check to see if all the results were successful
  #on failures notify the admins and send a message to the irc
  for (success, ping_result) in result_queue:
    if not success:
      ALL_MACHINES_RUNNING = False
      error_message += ping_result+"\n"

  #if all machines were pinged successfully, notify on irc if option -m was used to run ping_machines.py
  if ALL_MACHINES_RUNNING:
    if len(sys.argv) >= 2 and sys.argv[1] == '-m':
      irc_seattlebot.send_msg("The machines: "+str(machine_list)+" were pinged successfully")

  else:
    integrationtestlib.notify(error_message, "Seattle machines down!")
    irc_seattlebot.send_msg(error_message) 

    
  print time.ctime() + " : Done pinging all machiens."
  print "--------------------------------------------"

if __name__ == "__main__":
  main()     
         
 
