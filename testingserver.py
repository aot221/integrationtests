
import socket
import time
import subprocess
import tarfile
import tempfile
import hashlib
import os
import shutil
import select
from repyportability import *
import repyhelper

# Get the advertisement methods
repyhelper.translate_and_import("centralizedadvertise.repy")

# Stores Username:Password
ALLOWED_USERS = {}

# Name of our configuration file
CONFIG_FILE = "server.cfg"
RELOAD_INTV = 60              # How long between reloading our configuration and advertising

# Advertisement info
AD_TTL = 120    # 2 minutes
TESTBEDS = "SEATTLE_TESTBEDS" # Master advertisekey

def get_message(socket, digits=4,status=False):
  # Get the length of the user message
  length = int(socket.recv(digits))
  
  # Get the message
  message = ""
  remaining = length
  while remaining > 0:
    if status: print "Bytes Remaining:",remaining
    part = socket.recv(remaining)
    additional = len(part)
    if additional == 0:
      raise Exception, "Connection Terminated!"
    else:
      remaining -= additional
      message += part
  
  return message

def authenticate_connection(socket):
  # Get the user message
  message = get_message(socket)

  # Split the message
  (user,password) = message.split(";",1)
  
  # Check for authentication
  authenticated = False
  if user in ALLOWED_USERS and password == ALLOWED_USERS[user]:
    authenticated = True
 
  # Formulate a response
  response = str(authenticated).ljust(8) 
  
  # Respond, return status
  socket.send(response)
  return authenticated

def get_file(socket):
  # Get the message
  message = get_message(socket, 8)
  print "Received File Upload..."
 
  # Split
  precalchash = message[:32]
  actualmessage = message[32:]

  # Calculate the Hash
  print "Calculating Hash..."
  hash = hashlib.md5(actualmessage).hexdigest()   
  
  # Check that the hashes match
  match = (hash == precalchash)
  print "Hash Match:",match

  # Respond
  print "Sending Response..."
  response = str(match).ljust(8)
  socket.send(response)

  return actualmessage

def setup_environ(filecontents):
  # Create a temporary directory
  tmpdir = tempfile.mkdtemp()
  
  # Save the tar file
  tarfilename = os.path.join(tmpdir,"files.tar")
  fileh = open(tarfilename,"w")
  fileh.write(filecontents)
  fileh.close()

  # Store the CWD
  originaldir=os.getcwd()
  
  # Go to the temporary directory
  os.chdir(tmpdir)
  try:
    # Extract the files
    tar = tarfile.open("files.tar")
    tar.extractall()
    tar.close()
    
    # Delete the archive
    os.remove("files.tar") 
  finally:
    # Go to the original directory
    os.chdir(originaldir)
 
  return tmpdir
  
CHUNK_SIZE=512
SAMPLE_RATE = 0.1

# Run the test, streams results back to the user in chunks
def run_test(arguments, tmpdir, socket):
  # Go into the temporary directory
  originaldir = os.getcwd()
  os.chdir(tmpdir)
  try:
    # Start time
    start = time.time()

    # Launch the process
    proc = subprocess.Popen("python "+arguments,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    
    # Read the data from stdout and send it, timeout after 10 minutes
    while proc.poll() == None and time.time() - start < 600:
      try:
        # Check for ready sockets
        (rdy,wrt,excep) = select.select([proc.stdout, proc.stderr],[],[],SAMPLE_RATE)
      except Exception, e:
        rdy = []
      
      # Get data from each ready handle
      data = ""
      for handle in rdy:
        data += handle.read(CHUNK_SIZE)
      # If there is any data, write it out
      if data != "":
        socket.send(data)
 
    # Done, flush any remaining data
    data = proc.stdout.read()
    data += proc.stderr.read()
    if data != "":
      socket.send(data)
    proc.stdout.close()
    proc.stderr.close()

    # Kill the process if it is still running
    pid = proc.pid
    if proc.poll() == None:
      import nonportable
      nonportable.portablekill(pid)
  
  finally:
    os.chdir(originaldir)  

# Cleanup the state
def cleanup_environ(tmpdir):
  # Remove everything
  shutil.rmtree(tmpdir, True)

def connection_handler(remoteip, remoteport, socket, sockh, waith):
  # Try to handle the request. Log failures and always close the socket.
  try:
    # Check if the connection is authenticated
    print "New Connection! Authenticating..."
    authenticated = authenticate_connection(socket)
    if not authenticated:
      raise Exception, "Bad Auth!"

    # Get the file
    print "Downloading tar ball..."
    filecontents = get_file(socket)
    
    try:
      # Setup the test directory
      print "Extracting Tar File. Setting up environment..."
      tmpdir = setup_environ(filecontents)
      filecontents = None # Un-allocate the memory    

      # Get the user arguments
      arguments = get_message(socket)
   
      # Run the test!
      print "Running Test..."
      run_test(arguments, tmpdir, socket)
    
    finally:
      # Cleanup
      print "Cleaning up..."
      cleanup_environ(tmpdir)

  except Exception, e:
    try:
      socket.send("Exception Generated!!!! "+str(e))
    except:
      pass
    print remoteip+":"+str(remoteport)+"--","Generated Exception:",str(e)

  finally:
    try:
      socket.close()
    except:
      pass

# Updates server configuration, returns dictionary containing IP's, and hostnames
def update_configuration():
  # Store the configuration
  # We will read user names and passwords, our advertisement name
  # and our ips to listen on (only valid at start)
  configuration= {"users":[],"hostname":None,"ips":[]} 
 
  if os.path.exists(CONFIG_FILE):
    # Read the contents of the file
    fileh = open(CONFIG_FILE)
    config = fileh.readlines()
    fileh.close()
  
    for line in config:
      # Explode the configuration
      line = line.split()
      
      # Switch on the first part
      if line[0] == "hostname":
        configuration["hostname"] = line[1]
      elif line[0] == "user":
        # Append the user name and password
        configuration["users"].append((line[1],line[2]))  
      elif line[0] == "ip":
        configuration["ips"].append(line[1])

  # Reset the passwords
  ALLOWED_USERS.clear()
  for (user,passw) in configuration["users"]:
    ALLOWED_USERS[user]=passw
  
  # Return our configuration
  return configuration

def main():
  # Get our initial configuration
  config = update_configuration()
  print "Configured with hostname:",config["hostname"]
  
  # Always respond on getmyip() as well
  DEFAULT_IP = getmyip()
  config["ips"].append(DEFAULT_IP)
 
  # Check for other IP's, passed by command line or configuration
  for ip in sys.argv[1:]+config["ips"]:
    waitforconn(ip,50000,connection_handler)
    print "Responding on:",ip

  # Loop, always advertising us and reloading the configuration
  while True:
    # Do not override original config, since we won't change our listening IP's
    config_reloaded = update_configuration()

    # Check if our hostname is set
    if config_reloaded["hostname"]:
      # Advertise our hostname under the master list
      centralizedadvertise_announce(TESTBEDS,config_reloaded["hostname"],AD_TTL)
 
      # Advertise our IP under our own name
      advertise_key =  "SEATTLE_TESTBED_"+config_reloaded["hostname"]
      for ip in config["ips"]:
        centralizedadvertise_announce(advertise_key, ip, AD_TTL)
      
    # Sleep for a while
    time.sleep(RELOAD_INTV)  

if __name__ == "__main__":
  main()


