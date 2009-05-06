import subprocess
import getopt
import sys
import time

# Sample rate, 1 minute
SAMPLE=60

def main():
  # Parse the options
  options, args = getopt.getopt(sys.argv[1:], "", ["user=","pass=","host=","dir=","args="])
  
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

