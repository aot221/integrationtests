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



def monitor_seattle():
  """
  <Purpose>
    Checks to make sure that the critical processes on the machine 'seattle' are still running

  <Exceptions>
    None

  <Return>
    None
  """

  monitor_process_list=['advertiseserver.py']
  #build up the generic command
  command = "ps auwx | grep python | grep -v grep | grep geni| awk '{print $14}'"
  #command = 'ps auwx | grep python | grep -v grep | grep geni'
  
  #run a command on the linux machine to find all the relevant processes
  relevant_processes = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout  
  
  processes_string=""
  
  #make a string of all the processes
  for line in relevant_processes:
    processes_string = processes_string+line
  
  for critical_process in monitor_process_lists:
    if not critical_process in process_string:
	  print 'warning warning'
	else
	  print success

  
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
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    log(explanation_str)
    sys.exit(0)  
	
  if sys.argv[1] == '-seattle':
    monitor_seattle()
  elif sys.argv[1] == '-seattlegeni':
    monitor_seattlegeni()

	
	
if __name__ == "__main__":
  main()