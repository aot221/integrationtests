"""
<Program Name>
  resetblackboxupdate.py
  
<Started>
  December 17, 2008
  
<Author>
  Brent Couvrette
  couvb@cs.washington.edu
  
<Purpose>
  This script sets up the environment for pushsoftareupdate to run correctly.
  This includes running it through the repy preprocessor, making sure it knows
  where all its imports are, clearing out the blackbox update site, initializing
  the current_folder_num, current_key_num, and current_update_num files, creating
  the initial keypair, and creating the initial installers to be used.
  
<Usage>
  This script should be run once before starting the update blackbox test cron
  job.  After that, it should only be run again if the blackbox test system 
  becomes so corrupt that it needs to be completely started over.
  
  Note that it makes use of the constants in pushsoftwareupdate, so that should
  be confirmed correct before running this.
  
  Also note that for simplicity, this uses some linux specific features.
"""

import subprocess
import os

# Runs the repy preprocessor on pushsoftwareupdate.mix, then imports
# the resulting pushsoftwareupdate.py.  Assumes that we are running from
# within the integrationtests folder in a standard svn checkout of trunk.
def preprocess():
  # Move to the seattlelib directory
  orig_dir = os.getcwd()
  os.chdir('../seattlelib/')
  # Run the preprocessor
  subprocess.call('python repypp.py ../integrationtests/pushsoftwareupdate.mix \
      ../integrationtests/pushsoftwareupdate.py', shell=True)
  # Get back to our original directory
  os.chdir(orig_dir)
  # Need to copy over certain files so that the import repyportability works.
  subprocess.call('cp ../portability/repyportability.py ../repy/* .', 
      shell=True)
  # Need to copy over certain files so that the import make_base_installers
  # works.
  subprocess.call('cp ../dist/make_base_installers.py ../dist/clean_folder.py \
      ../dist/build_installers.py .', shell=True)
  # Importing pushsoftwareupdate should now be successful.
  print "Finished preprocessing"


# clears out the folder specified as the root of the update site in
# pushsoftwareupdate.py.  Also clears out the folder containing the keypairs
# in the current directory.  We only remove the specific things we make,
# just in case say the update_base_directory gets set to /.  Just doing
# rm -r * there would almost certainly be extremely devastating.
def clear_blackbox():
  import pushsoftwareupdate
  # Remove the file keeping track of the folder number
  subprocess.call('rm ' + pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.foldernum_fn, shell=True)
  # Remove the file keeping track of the key number
  subprocess.call('rm ' + pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.keynum_fn, shell=True)
  # Remove the file keeping track of the update number
  subprocess.call('rm ' + pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.updatenum_fn, shell=True)
  # Remove all update folders
  subprocess.call('rm -r ' + pushsoftwareupdate.update_base_directory + 
      'update_location*', shell=True)
  # Remove any current installed files
  subprocess.call('rm -r ' + pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.installer_folder, shell=True)
  # Remove all previous keypairs
  subprocess.call('rm -r ' + pushsoftwareupdate.key_folder, shell=True)
  print "Finished clearing"


# Creates and initializes the counting files
def init_counts():
  import pushsoftwareupdate
  # init the folder count
  numfile = open(pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.foldernum_fn, 'w')
  numfile.write('0')
  numfile.close()
  # init the key count
  numfile = open(pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.keynum_fn, 'w')
  numfile.write('0')
  numfile.close()
  # init the update count
  numfile = open(pushsoftwareupdate.update_base_directory + 
      pushsoftwareupdate.updatenum_fn, 'w')
  numfile.write('0')
  numfile.close()
  print "Finished creating count files"


# Creates the folder to contain the keys, as well as the first keypair
def init_first_keys():
  import pushsoftwareupdate
  os.mkdir(pushsoftwareupdate.key_folder)
  pushsoftwareupdate.makekeys(0)
  print "Finished making keys"


# Creates the installer folder, as well as the initial installers
def init_first_installers():
  import pushsoftwareupdate
  os.mkdir(pushsoftwareupdate.update_base_directory +
      pushsoftwareupdate.installer_folder)
  trunk = pushsoftwareupdate.svn_trunk_location
  pubkey = pushsoftwareupdate.key_folder + 'pubkey0'
  privkey = pushsoftwareupdate.key_folder + 'privkey0'
  updatesite = pushsoftwareupdate.update_base_url + 'update_location0'
  pushsoftwareupdate.create_installers(trunk, pubkey, privkey, updatesite,
      pubkey, 0)
  print "Finished making installers"
      

def main():
  preprocess()
  clear_blackbox()
  init_counts()
  init_first_keys()
  init_first_installers()


if __name__ == "__main__":
  main()
