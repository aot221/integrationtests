"""
<Program Name>
  monitor_processes.py
  
<Started>
  June 9, 2009
  
<Author>
  Monzur Muhammad
  monzum@u.washington.edu
"""

import subprocess
import sys
import send_gmail
import irc_seattlebot

# the people to notify on failure/if anything goes wrong
notify_list = ["ivan@cs.washington.edu, justinc@cs.washington.edu", "monzum@u.washington.edu"]

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
  subj = "seattle critical process down @ " + hostname + " : " + sys.argv[0]
  
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



def monitor_processes(monitor_process_list, command_list):
  """
  <Purpose>
    Checks to make sure that the critical processes on the machine 'seattle' are still running

  <Exceptions>
    None

  <Arguments>
    monitor_process_list - a list of all the critical processes that should be checked to 
      see if they are up and running.

    command_list - a list of all the commands required to find all the relevant processes

  <Return>
    None
  """
  
  #string that holds the name of all the processes that are found to be running using the
  #ps commands that was passed in as argument
  processes_string=""
  
  #run a command on the linux machine to find all the relevant processes
  for command in command_list:
    relevant_processes = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout  

    #make a string of all the processes
    for line in relevant_processes:
      processes_string = processes_string+line
 
  #keeps track to see if any processes are down 
  critical_process_down=False
  error_message="WARNING: Critical processes down! Seattle developers please start the processes up as soon as possible\n"
  error_message=error_message+"Listing processes that are down:\n"

  #goes through the list of monitor_process_list to ensure that all processes are running
  for critical_process in monitor_process_list:
    if not critical_process in processes_string:
      critical_process_down=True
      error_message = error_message+critical_process+" is down on seattle.cs.washington.edu\n"
  
  error_message=error_message+"end of list of processes that are down.\n................................"
  if critical_process_down:
    #handle_exception(error_message)
    irc_seattlebot.send_msg(error_message)


def main():
  """
  <Purpose>
    Runs at regular time intervals to make sure that critical processes on a machine
    are still up and running. If a critical process is not running then system admins
    are sent an email, as well as a message is posted on the IRC.
	
  <Exceptions>
    None

  <Usage>
    This script takes no arguments. A typical use of this script is to
    have it run periodically using something like the following crontab line:  
	
    */15 * * * * export GMAIL_USER='username' && export GMAIL_PWD='password' && /usr/bin/python /home/seattle/monitor_scripts/monitor_processes.py > 
    /home/seattle/monitor_scripts/cron_log.monitor_processes
  """
  
  # setup the gmail user/password to use when sending email
#  success,explanation_str = send_gmail.init_gmail()
 # if not success:
  #  log(explanation_str)
   # sys.exit(0)  

  #processes that should be running on seattle server
  seattle_process_list=['advertiseserver.py', 'blah']	

  #The commands that should be run on seattle to get all the required processes
  seattle_command = ["ps auwx | grep python | grep -v grep | grep geni | awk '{print $14}'"]

  #processes that should be running on seattlegeni server
  seattlegeni_process_list=['expire_vessels.py', 'donationtocanonical.py', 'canonicaltoonepercent_manyevents.py', 'dbnode_checker.py', 'apache2', 'mysqld']

  #The commands that should be run on seattlegeni to get all the required processes  
  seattlegeni_command = ["ps auwx | grep python | grep -v grep | grep geni | awk '{print $12}'"]
  seattlegeni_command.append("ps auwx | grep apache | grep -v grep | grep root | awk '{print $11}'")
  seattlegeni_command.append("ps auwx |grep mysqld |grep root | awk '{print $12}'")
 
  #run monitor processes with the right command
  if sys.argv[1] == '-seattle':
    monitor_processes(seattle_process_list, seattle_command)
  elif sys.argv[1] == '-seattlegeni':
    monitor_processes(seattlegeni_process_list, seattlegeni_command)

	
	
if __name__ == "__main__":
  main()
