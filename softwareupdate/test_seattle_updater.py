#!/usr/bin/python
"""
<Program Name>
  test_seattle_updater.py

<Purpose>
  Verify that the current Seattle release can update.

<Usage>
  Modify the following global var params to have this script functional:

  - seattle_linux_url, the url of the seattle distro to download and update.

  - integrationtestlib.notify_list, a list of strings with emails denoting who will be
    emailed when something goes wrong

  This script takes no arguments. A typical use of this script is to
  have it run periodically using something like the following crontab line:
  0 14 * * * /usr/bin/python /home/seattle/softwareupdater_tests/test_software_updater.py >> /home/seattle/cron_log.test_software_updater 2>&1
"""

import time
import os
import sys
import traceback
import urllib2
import signal
import subprocess
import send_gmail
import integrationtestlib

# path test_directory where we will download seattle
test_directory = os.getcwd()

# the url from where we will fetch a linux version of seattle
seattle_linux_url = "https://seattleclearinghouse.poly.edu/download/seattle_install_tester/seattle_linux.tgz"

REPY_RELATIVE_PATH = "seattle/seattle_repy/"


def cleanup():
  """
  <Purpose>
   Cleans up any files created by this test.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    Removes the downloaded installer, metainfo file and the Seattle
    directory.

  <Returns>
    None.
  """
  # remove all traces
  integrationtestlib.log("We are now done! Removing installation files.")
  os.system("rm -Rf " + test_directory + "/metainfo")
  os.system("rm -Rf " + test_directory + "/seattle/")
  os.system("rm -Rf " + test_directory + "/seattle_linux.tgz")


def download_and_unpack_seattle():
  """
  <Purpose>
    Downloads and unpacks Seattle

  <Arguments>
      None.

  <Exceptions>
      None.

  <Side Effects>
    Downloads the seattle installer tar-gzip file and unpacks it.
    If the file already exists in the test directory, we overwrite it.

  <Returns>
      None.
  """

  if os.path.isfile(test_directory+"/seattle_linux.tgz"):
    os.remove(test_directory+"/seattle_linux.tgz")

  integrationtestlib.log("downloading distro for seattle_install_tester...")
  os.system("wget --no-check-certificate " + seattle_linux_url)
  integrationtestlib.log("unpacking...")
  os.system("tar -xzvf " + test_directory + "/seattle_linux.tgz")


def get_metainfo_hashes(metainfo):
  """
  <Purpose>
    Converts a metainfo file into a dictionary mapping filenames to
    hashes.

  <Arguments>
    metainfo:
      A string representing the contents of a metainfo file, obtained
      from Seattle's updater site.

  <Side Effects>
    None

  <Exceptions>
    If the metainfo file is malformed, an Exception is raised.

  <Returns>
    A dictionary mapping filenames to their hashes.
  """
  metainfo_dict = {}
  # This code is adapted from the softwareupdater file.
  for line in metainfo.splitlines():
    # skip blank lines
    if not line.strip():
      continue

    # skip comments
    if line[0] == '#':
      continue

    # skip signature parts
    if line[0] == '!':
      continue

    linelist = line.split()
    if len(linelist)!= 3:
      raise Exception("Malformed metainfo line: '"+line+"'")

    filename, filehash, filesize = linelist
    metainfo_dict[filename] = filehash
  return metainfo_dict


def start_updater_process():
  """
  <Purpose>
    Starts the software updater process.

  <Arguments>
    None

  <Side Effects>
    The current working directory will temporarily switch to the
    directory where softwareupdater resides.  Upon exiting this
    function, we will always be back at the working directory before
    calling this function.

  <Exceptions>
    Shouldn't be any, unless the starting of the software updater fails.

  <Returns>
    The PID of the started process.
  """
  try:
    working_directory_before = os.getcwd()
    os.chdir(REPY_RELATIVE_PATH)
    process = subprocess.Popen([sys.executable, "softwareupdater.py"])
    return process.pid
  finally:
    os.chdir(working_directory_before)


def main():
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  updater_pid = None

  repy_path = test_directory + os.sep + REPY_RELATIVE_PATH
  logfile_name = "softwareupdater.old"
  logfile_path = repy_path + logfile_name

  # Wrap in a try...except so that the test stops running once we run
  # into an error.  We also want to unconditionally cleanup the test
  # files, so that subsequent tests start fresh.
  try:
    download_and_unpack_seattle()

    # We want to make sure that the installed versions can update, so we
    # need to get the URL from the softwareupdater from within the
    # installer.  Because of this, we have no choice but to delay the
    # import until now, otherwise the module would not yet exist.
    sys.path.insert(0, REPY_RELATIVE_PATH)
    import softwareupdater
    metainfo_url = softwareupdater.softwareurl + 'metainfo'

    # Retrieve the update metainfo file.
    metainfo = urllib2.urlopen(metainfo_url).read()
    # The metainfo file may be useful for debugging purposes if
    # something goes wrong.
    open(test_directory + os.sep + 'metainfo', 'w').write(metainfo)

    hashes = get_metainfo_hashes(metainfo)

    # I think its safe to assume that each release will always have this
    # file...
    file_to_modify_name = "nmmain.py"
    file_to_modify_path = repy_path + file_to_modify_name

    # We don't particularly care how this file is modified, as long as
    # its hash changes.  It should be okay if we append some data to the
    # end of the file.
    file_to_modify = open(file_to_modify_path, 'a')
    file_to_modify.seek(0, 2)
    file_to_modify.write("\n# An update should remove this line\n")
    file_to_modify.close()

    # The updater will take some time to run...
    updater_pid = start_updater_process()

    integrationtestlib.log("sleeping for 60 minutes...")
    time.sleep(60 * 60)

    # We have to assume that the metainfo file didn't change since we
    # downloaded it, so this may give us some false negatives if a push
    # was done after we retrieved the metainfo file.
    if softwareupdater.get_file_hash(file_to_modify_path) != hashes[file_to_modify_name]:
      # Maybe the signature expired?
      updater_log = open(logfile_path, 'r')
      last_line = updater_log.readlines()[-1].strip()
      updater_log.close()

      if "[do_rsync] Something is wrong with the metainfo: ['Expired signature', 'Expired signature']" in last_line:
        # Not sure if we should notify the administrators about this one...
        raise Exception("Metainfo signature expired!")
      elif "Another software updater old process" in last_line:
        raise Exception("Seattle failed to update because another software updater is currently running!  Please investigate what is causing the extra updater to run.")
      else:
        # Something really bad happened...
        raise Exception("Seattle failed to restore the modified file to the updated version. If there was a new release of Seattle done in the last hour, then it is possible that this is a false negative.")

    # Make sure that we actually got a chance to run, since only one
    # instance of the software updater is supposed to be running on each
    # machine.
    updater_log = open(logfile_path, 'r')
    last_line = updater_log.readlines()[-1].strip()
    updater_log.close()

  except Exception, e:
    backup_directory_name = "backup-" + time.strftime("%Y-%m-%d-%H:%M:%S")

    text = "The updater integration test failed!\n"
    text += "The seattle directory will be backed up to: '"+backup_directory_name+"'\n"
    text += "In addition, the metainfo file and the downloaded seattle_linux.tgz will also be in the backup directory.\n"
    text += "----------------------------\n"
    text += traceback.format_exc()
    integrationtestlib.log(text)
    integrationtestlib.notify(text, "Seattle Update Test Failed!")

    # Since something bad happened, we want to keep the directory
    # intact, in case it helps with any debugging.
    backup_seattle_directory_path = backup_directory_name + os.sep + "seattle"
    os.makedirs(backup_seattle_directory_path)
    os.rename("seattle", backup_seattle_directory_path)
    os.rename("metainfo", backup_directory_name + os.sep + "metainfo")
    os.rename("seattle_linux.tgz", backup_directory_name + os.sep + "seattle_linux.tgz")

    # We do some cleaning up after, so update the log path
    logfile_path = backup_seattle_directory_path + os.sep + "seattle_repy/" + logfile_name

  finally:
    # We don't want this software updater process to interfere with
    # anything else if possible...
    # If the software updater restarted itself, kill it as well
    # We can extract the PID from the logfile.
    updater_log = open(logfile_path, 'r')
    last_line = updater_log.readlines()[-1].strip()
    updater_log.close()

    # The software updater log file looks like this...
    # 1386093513.87:PID-86718:[fresh_software_updater] Fresh software updater started.
    updater_pid = int(last_line.partition('PID-')[2].partition(':')[0])

    if updater_pid is not None:
      integrationtestlib.log("Terminating updater process " + str(updater_pid))
      os.kill(updater_pid, signal.SIGKILL)

    cleanup()


if __name__ == "__main__":
    main()
