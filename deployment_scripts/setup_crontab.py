"""
<Program Name>
  setup_crontab.py

<Started>
  May 22, 2009

<Author>
  Monzur Muhammad
  monzum@u.washington.edu
"""

import os
import tempfile
import re
import sys
import subprocess

try:
  import nonportable
except ImportError:
  raise ImportError, "Error importing nonportable, make sure that nonportable is in your PYTHONPATH"


#get the os of system
OS = nonportable.ostype

#Exception that is raised if cron job exists in cron tab
class PreviousCronJobExists(Exception):
  pass

#Exception for unsupported OS (only Linux is supported for the crontab)
class UnsupportedOSError(Exception):
  pass

#Exception for import error
class ImportError(Exception):
  pass

def add_crontab(crontab_line, cron_name):
  """
  <Purpose>
    To setup a job using crontab on a Linux machine ONLY.

  <Exceptions>
    If OS is not Linux, then the crontab setup will not work and throw an
    UnsupportedOSError exception.
    Throws an PreviousCronJobExists if the crontab already contains a line with
    the job that the user is trying to setup

  <Usage>
    add_crontab(<crontab_line>, <cron_name>)
    The purpose of the cron_name is purely to check that a previous job has not
    been created.

  <Result>
    Returns true if the crontab was setup properly

  """
 
  global OS

  #make sure that we are on a linux machine
  if OS != "Linux":
    raise UnsupportedOSError

 
  crontab_current, crontab_error = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).communicate()

 
  #creates a temporary file to hold all the current cronjobs
  temp_cronfd, temp_filename = tempfile.mkstemp("temp", "crontab")

  #check to see if the job is already in the crontab
  #if the job exists then close all files and raise an exception
  #else take the current line from the cron tab and add it to the temporary file
  for line in crontab_current.split('\n'):
    if re.search(cron_name, line):
      crontab_current.close()
      os.close(temp_cronfd)
      os.unlink(temp_filename)
      raise PreviousCronJobExists
    else:
      os.write(temp_cronfd, line+os.linesep)

  #add the new line to the cron tab, the line that was provided by the user
  os.write(temp_cronfd, crontab_line) 
  os.close(temp_cronfd)

  #replace the old crontab with the crontab that was created
  #in the temporary file.
  subprocess.Popen("crontab '" + temp_filename + "'", shell=True, stdout=subprocess.PIPE).communicate()

  #unlink and release the tempfile
  os.unlink(temp_filename)
 
  return True
   
   
 
    
  
    

  

