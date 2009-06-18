"""
<Program Name>
  deploy_downloadandinstallseattle.py

<Started>
  May 20, 2009

<Author>
  Monzur Muhammad
  monzum@u.washington.edu
"""

import os
import sys
import setup_crontab
import glob

try:
  import preparetest
except ImportError:
  raise ImportError, "Error importing preparetest, make sure that preparetest is in your PYTHONPATH"


def main():
  """
  <Purpose>
    Deploys the downloadandinstallseattle.py along with all the files needed into a
    single directory. The directory must already exist.

  <Exceptions>
    If OS is not Linux, then setting up crontab will not work.
	
  <Side Effect>
    If the target directory that the user provides is not empty, then this script will delete all the files
    that already exist in that directory.	

  <Usage>
    make a folder that lies in the same directory as the trunk director and copy this file and setup_crontab.py in that file. Go to the trunk folder in the svn checkout directory and run the command: python preparetest.py <../folder_name>. Then copy over preparetest.py in that folder as well.  
    PYTHONPATH=$PYTHONPATH:/home/<user_name>/trunk && deploy_downloadandinstallseattle.py <target_folder>

  """

  checkArgs()

  #setup some variables for cron setup
  cron_setup = False
  log_dir = ""

  # -c means we have to setup the crontab with a new cron job
  if sys.argv[1] == '-c':
    cron_setup = True
    sys.argv = sys.argv[1:]
    checkArgs(cron_setup)
    log_dir = sys.argv[2]
    
    if not( os.path.isdir(log_dir) ):
      help_exit("given log_foldername is not a directory")

  #set up all the variables about directory information
  current_dir = os.getcwd()
  
  #ensures that the backslashes and forward slashes are proper for the OS
  target_dir = os.path.normpath(sys.argv[1])

  #make sure svn is up to date and start up preparetest
  os.chdir(os.path.normpath(current_dir + "/../trunk"))
  os.system("svn up")
  os.chdir(current_dir)
  preparetest.main()

  if not( os.path.isdir(target_dir) ):
    help_exit("given foldername is not a directory")

  #change to target directory and clean up the target directory folder
  os.chdir(target_dir)

  files_to_remove = glob.glob("*")

  for f in files_to_remove:
    if os.path.isdir(f):
      shutil.rmtree(f)
    else:
      os.remove(f)

  os.chdir(current_dir)
  
  #the next few lines is necessary unless the file is manually copied over
  preparetest.copy_to_target("../trunk/integrationtests/downloadandinstallseattle/*", target_dir)
  preparetest.copy_to_target("../trunk/integrationtests/common/*", target_dir)
  
  #change directory to the target directory and preprocess the *.mix files
  os.chdir(target_dir)
  preparetest.process_mix("repypp.py")
  

  #check to see if cron setup was requested, if yes run cron_setup
  if cron_setup:

    #create the absolute path for the log file and the file needed for the 
    #cron job
    cron_tab_dir=os.path.normpath(current_dir + "/" + target_dir)
    cron_log_dir=os.path.normpath(current_dir + "/" + log_dir)
    
    cron_line="15 16 * * * export GMAIL_USER='seattle.devel@gmail.com' && export GMAIL_PWD='repyrepy' && /usr/bin/python " + cron_tab_dir + "/downloadandinstallseattle.py >> " + cron_log_dir + "/cron_log.downloadandinstallseattle 2>&1" + os.linesep

    #setup the cron job
    setup_crontab.add_crontab(cron_line, "downloadandinstallseattle")
    



#checks to make sure that the right amount of arguments are provided  
def checkArgs(cron=False):

  if cron and len(sys.argv) < 3:
    help_exit("Invalid number of arguments with option -c, need <log_directory>")
    
  elif len(sys.argv) < 2:
    help_exit("Invalid number of arguments")
   
  

#exit program with a message and help menu
def help_exit(exit_msg):
  print exit_msg
  option_message = "Options:\n -c\tsetup crontab"
  print "python deploy_downloadandinstallseattle.py [option] <target_directory> [<log_directory>]"
  print option_message
  sys.exit(1)

if __name__ == "__main__":
  main()

