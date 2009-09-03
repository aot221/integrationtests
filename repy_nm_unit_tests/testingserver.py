"""
Author: Armon Dadgar
Date: Early May, 2009
Description:

  This script is meant to run on a server, and it serves as a seattle testbed.
  The server will automatically advertise itself and wait for incoming connections.
  Incoming connections are authenticated, and then a gzipped tar file is uploaded to the server.
  The server will extract this to a temporary directory, and then chdir into the directory.
  Finally, the client will upload some arguments. 'python ' is pre-pended to those arguments,
  and then executed in the temporary directory. The server will then read the data from stdout and stderr,
  and send it to the client. Once finished, the socket will be closed, the test process killed if necessary,
  and the temporary directory deleted.

"""

import socket
import sys
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
import harshexit

# Get the advertisement methods
repyhelper.translate_and_import("centralizedadvertise.repy")

# Stores Username:Password
ALLOWED_USERS = {}

# Name of our configuration file
CONFIG_FILE = "server.cfg"
RELOAD_INTV = 60              # How long between reloading our configuration and advertising
INITIAL_CONFIG = {}           # Initially loaded config file, only the initial

# Advertisement info
AD_TTL = 120    # 2 minutes
TESTBEDS = "SEATTLE_TESTBEDS" # Master advertisekey

def get_message(socket, digits=4,status=False):
  """
  <Purpose>
    Retrieves a full messsage from the socket. Each message is prepended with 'digits' number of digits,
    which indicate the length of the proceding message.

  <Arguments>
    socket: A TCP socket
    digits: Defaults to 4, the number of prepended digits to check for.
    status: If true, it will print the bytes remaining to be downloaded.

  <Returns>
    The message.
  """

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
  """
  <Purpose>
    Authenticates the current connection. A username/password combo is transmitted to the server,
    and we check against the ALLOWED_USERS dictionary to see if this is valid.

  <Arguments>
    socket: A TCP socket.

  <Returns>
    True if authenticated, False otherwise.
  """
  # Get the user message
  message = get_message(socket)

  # Split the message
  (user,password) = message.split(";",1)
   
  # Check for authentication
  authenticated = False
  if user in ALLOWED_USERS and password == ALLOWED_USERS[user]:
    authenticated = True
  print "User:",user,", Authenticated:",authenticated 

  # Formulate a response
  response = str(authenticated).ljust(8) 
  
  # Respond, return status
  socket.send(response)
  return authenticated

def get_file(socket):
  """
  <Purpose>
    Downloads the gzipped tarfile from the client. The file is checked against its MD5 hash to check for a match.
    * Limitation: The server will continue if the tarfile is corrupt, however the client is designed to terminate,
    which will cause the server to terminate as well.

  <Arguments>
    socket: A TCP socket.

  <Returns>
    The contents of the gzipped tarfile.
  """

  # Get the message
  message = get_message(socket, 8)
 
  # Split
  precalchash = message[:32]
  actualmessage = message[32:]

  # Calculate the Hash
  hash = hashlib.md5(actualmessage).hexdigest()   
  
  # Check that the hashes match
  match = (hash == precalchash)
  print "Hash Match:",match

  # Respond
  response = str(match).ljust(8)
  socket.send(response)

  return actualmessage

def setup_environ(filecontents):
  """
  <Purpose>
    Setups a temporary directory to run the user test.

  <Arguments>
    The contents of the gzipped tarfile.

  <Returns>
    The full path to the temporary directory.
  """

  # Create a temporary directory
  tmpdir = tempfile.mkdtemp()
  
  # Save the tar file
  tarfilename = os.path.join(tmpdir,"files.tar")
  fileh = open(tarfilename,"wb")
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


# Helps stop the test
def stoptest(socket,pid):
  """
  <Purpose>
    Checks the socket for any incoming user messages while the test is running.
    If the user sends 'cancel' to us, we will kill the running test.
  
  <Arguments>
    socket: A TCP socket to read from
    pid: The PID of the process to kill.
  """

  try:
    mesg = socket.recv(8)
    print "Incoming message:",mesg
    if "cancel" in mesg:
      harshexit.portablekill(pid)
  except:
    pass

CHUNK_SIZE=512
SAMPLE_RATE = 0.1

# Run the test, streams results back to the user in chunks
def run_test(arguments, tmpdir, socket):
  """
  <Purpose>
    Runs the actual test while streaming the results back to the user.

  <Arguments>
    arguments: The command to executed, will be prepended with 'python '
    tmpdir: The temporary directory which we should execute in
    socket: A TCP socket to stream the results back on.

  <Side Effects>
    Launches a new process.

  <Returns>
    Nothing.
  """
  global INITIAL_CONFIG
  enable_stderr = INITIAL_CONFIG["stderr"]
  path = INITIAL_CONFIG["path"]
  use_shell = INITIAL_CONFIG["shell"]

  # Inform the user what is happening  
  if not enable_stderr:
    socket.send("NOTE: stderr will be deferred until program exits.\n")

  # Go into the temporary directory
  originaldir = os.getcwd()
  os.chdir(tmpdir)
  try:
    # Start time
    start = time.time()

    # Launch the process
    proc = subprocess.Popen(path+" "+arguments,shell=use_shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    pid = proc.pid 
   
    # Setup a thread to check for an interrupt request
    settimer(0, stoptest,(socket,pid))

    # Read the data from stdout and send it, timeout after 10 minutes
    while proc.poll() == None and time.time() - start < 600:
      # Enable stderr by default, disable on some systems (Windows)
      # On windows select cannot be used, defer stderr
      if enable_stderr:
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
      else:
        # Only check stderr until the then
        data = proc.stdout.read(CHUNK_SIZE)
        if data != "": socket.send(data)
        time.sleep(SAMPLE_RATE)        

    # Done, flush any remaining data
    data = proc.stdout.read()
    data += proc.stderr.read()
    if data != "":
      socket.send(data)
    proc.stdout.close()
    proc.stderr.close()

    # Kill the process if it is still running
    if proc.poll() == None:
      harshexit.portablekill(pid)
  
  finally:
    os.chdir(originaldir)  

# Cleanup the state
def cleanup_environ(tmpdir):
  """
  <Purpose>
    Cleans up the test environment.

  <Arguments>
    tmpdir: The temporary directory
  """

  # Remove everything
  shutil.rmtree(tmpdir, True)

def connection_handler(remoteip, remoteport, socket, sockh, waith):
  """
  <Purpose>
    Handles incoming connection attempts.
    Processes requests in this order:
    1) Authenticate the connection, exit on failure.
    2) Download the tarfile
    3) Setup the test environment
    4) Download the test arguments
    5) Start the test and stream the results.
    6) Cleanup and close the socket.

  <Arguments>
    see waitforconn.

  <Returns>
    Nothing.
  """
  # Try to handle the request. Log failures and always close the socket.
  try:
    # Check if the connection is authenticated
    print round(time.time()),"-Connected IP:",remoteip,"Port:",remoteport
    authenticated = authenticate_connection(socket)
    if not authenticated:
      raise Exception, "Bad Auth!"

    # Get the file
    print "Downloading tar ball..."
    filecontents = get_file(socket)
    size = len(filecontents)
 
    # Setup the test directory
    print "Extracting Tar File. Size:",size,"Setting up environment..."
    tmpdir = setup_environ(filecontents)
    filecontents = None # Un-allocate the memory    
    
    try:
      # Get the user arguments
      arguments = get_message(socket)
      print "Argument:",arguments
 
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
  """
  <Purpose>
    Reloads the server configuration.
    Parses the server.cfg file and generates a configuration dictionary.
    This function updates the ALLOWED_USERS dictionary when called.

  <Notes>
    The server configuration file is of the following format:
    1) The first word on the line specifies the type of configuration.
    1.a) Valid config directives: hostname, user, ip, disablestderr
    2) hostname is followed after a space with the desired hostname of the server.
    This should not contain any spaces. E.g. 'hostname test_machine'
    3) The user directive is followed by 2 more 'words' a user name and a password
    Each should not contain any spaces. E.g. "user test testpassword"
    4) The ip directive tells the server what additional IP's to listen on.
    The server will always listen to the IP from getmyip().
    E.g. "ip 127.0.0.1"
    5) The disablestderr directive is for OS's which cannot use select.select on file descriptors.
    This is only applicable to Windows. What it does it only send stdout during run_test() and send
    the stderr output after the test has terminated. This is necessary to avoid blocking while the test
    is running.

    6) Sample configuration file:
    "
    hostname testmachine
    ip 127.0.0.1
    ip 192.168.1.1
    user test1 password1
    user test2 password2
    disablestderr
    "

  <Returns>
    The configuration dictionary.
  """
  global ALLOWED_USERS
  # Store the configuration
  # We will read user names and passwords, our advertisement name
  # and our ips to listen on (only valid at start)
  configuration= {"users":[],"hostname":None,"ips":[],"stderr":True,"path":"python","shell":True} 
 
  if os.path.exists(CONFIG_FILE):
    # Read the contents of the file
    fileh = open(CONFIG_FILE)
    config = fileh.readlines()
    fileh.close()
  
    for line in config:
      # Determine if the line is blank or a comment, then skip it
      if line.strip() == "" or line[0] == "#":
        continue

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
      elif line[0] == "disablestderr":
        configuration["stderr"] = False
      elif line[0] == "path":
        # Re-join the remainder of the line to form the path
        configuration["path"] = " ".join(line[1:])
      elif line[0] == "noshell":
        configuration["shell"] = False

  # Reset the passwords
  new_allowed = {}
  for (user,passw) in configuration["users"]:
    new_allowed[user]=passw
  ALLOWED_USERS = new_allowed

  # Return our configuration
  return configuration

def main():
  """
  <Purpose>
    It is the main function...
    It will do the following:
    1) Load the initial config, stored in INITIAL_CONFIG
    2) Setup waitforconn on all 'ip' entries and getmyip()
    3) Enter an infinite loop attempting to reload the configuration
    and advertising every minute. Updated the config allows users to be removed,
    added or updated while the server is running, without the need to stop.
  """
  global INITIAL_CONFIG

  # Get our initial configuration
  config = update_configuration()
  INITIAL_CONFIG = config
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

    try:
      # Check if our hostname is set
      if config_reloaded["hostname"]:
        # Advertise our hostname under the master list
        centralizedadvertise_announce(TESTBEDS,config_reloaded["hostname"],AD_TTL)
   
        # Advertise our IP under our own name
        advertise_key =  "SEATTLE_TESTBED_"+config_reloaded["hostname"]
        for ip in config["ips"]:
          centralizedadvertise_announce(advertise_key, ip, AD_TTL)
    except:
      # Ignore advertisement errors
      pass

    # Flush stdout and stderr
    sys.stdout.flush()
    sys.stderr.flush()
 
    # Sleep for a while
    time.sleep(RELOAD_INTV)  

if __name__ == "__main__":
  main()


