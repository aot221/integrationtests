"""
Author: Armon Dadgar
Date: Early May, 2009
Description:

  This is a simple wrapper around remotetest.py to allow running tests on multiple hosts concurrently.

"""

import subprocess
import getopt
import sys
import time

# Sample rate, 1 minute
SAMPLE=60

def main():
  """
  <Purpose>
    Runs remotetest.py on multiple hosts concurrently. Samples the test status and informs the user which
    hosts are finished.Does the following:

  1) Takes Almost the same options as remotetest.py. Does not take --ip, but takes multiple --host entries.
  1.a) Optionally takes a --sample flag which changes its sample rate from 60 seconds to anything.
  2) For each host, launch remotetest.py with the arguments we were passed, only giving 1 --host directive.
  3) Redirect the output for each host to host.result.txt. E.g. --host attu -> attu.results.txt
  4) Every SAMPLE seconds, defaults 60, checks the status of each host to see if it is still running,
  prints output to the inform the user which hosts have finished, so that they can view the results.

  """
  global SAMPLE

  # Parse the options
  options, args = getopt.getopt(sys.argv[1:], "", ["help","sample=","user=","pass=","host=","dir=","args="])
  
  config = {"user":None,"pass":None,"hosts":[],"dir":None,"args":None}  
  for (flag, val) in options:
    if flag == "--user":
      config["user"] = val
    elif flag == "--pass":
      config["pass"] = val
    elif flag == "--host":
      config["hosts"].append(val)
    elif flag == "--dir":
      config["dir"] = val
    elif flag == "--args":
      config["args"] = val
    elif flag == "--sample":
      SAMPLE=int(val)
    elif flag == "--help":
      print "Takes the same parameters as remotetest.py with some minor changes."
      print "Does not accept --ip, but allows multiple --host entries."
      print "Takes an optional --sample flag which changes the default sample rate (60 sec)."
      exit()

  # Build the generic command
  cmd = "python remotetest.py --user "+config['user']+" --pass "+config['pass']+" --dir "+config['dir']+" --args '"+config['args']+"' --host "
  
  processes = []
  for host in config["hosts"]:
    # Create an output file for the host
    filename = host+".result.txt"
    print "Storing output for",host,"in",filename
    outfile = open(filename,"w")

    # Launch the process, append the desired host
    print "Staring test on",host
    proc = subprocess.Popen(cmd+host, shell=True, stdout=outfile,stderr=outfile)
    
    # Store this process
    processes.append((host,outfile,proc))
    
    # Wait before starting the next process
    time.sleep(1)

  # Save the time
  start = time.time()

  while True:
    remaining = []
    time.sleep(SAMPLE)
    print "###" # A little space
    print "Checking at:",round(time.time()-start),"seconds..."
    for testrun in processes:
      (host,out,proc) = testrun
      done = not (proc.poll() == None)
      print "Host:",host,"Done:",done
      
      out.flush() # Flush the output
      if not done: remaining.append(testrun) # Store the process
      else: out.close()			     # Close the file handle
    
    # Only keep the non-finished tests
    processes = remaining
    if len(processes) == 0: break	# Stop when all processes finish

  print "Done running all tests!"


if __name__ == '__main__':
  main()

