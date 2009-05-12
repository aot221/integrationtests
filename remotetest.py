"""
Author: Armon Dadgar
Date: Early May, 2009
Description:

  Works with the testingserver.py to allow users to run test on remote testbeds.
  The script has several abilities: 1) To list available testbeds, 2) To get information
  about the available testbeds (IP addresses), 3) To launch a test on a remote testbed.

  NOTES:
  SEATTLE_TESTBEDS is the key used to lookup testbeds
  SEATTLE_TESTBED_$HOST , where $HOST is replaced with the real host is used to lookup
  an actual host and its IP's
  By default when running on a host, the _last_ ip in this list is used. This is because the
  getmyip address will always be the last in the list.

"""

from repyportability import *
import hashlib
import getopt
import tarfile
import time
import sys
import os
import repyhelper
import signal
import select

# Get the advertisement methods
repyhelper.translate_and_import("centralizedadvertise.repy")

# This dictionary can be used to hardcode hostname to IPs
# Otherwise, we fallback onto advertisement
HOSTS = {}
PORT = 50000

# Finds all available seattle testbeds
def find_testbeds():
  servers = centralizedadvertise_lookup("SEATTLE_TESTBEDS")
  return servers

# Finds the IP's of a specific testbed
def find_testbed(name):
  ip_addrs = centralizedadvertise_lookup("SEATTLE_TESTBED_"+name)
  return ip_addrs

# Connects to the proper host, returns socket
def connect_to_host(config):
  """
  <Purpose>
    Connects to the desired host. Parses config to determine what to do.
    If an --ip is given, that is used. If a --host is given, we first check
    the hardcoded hosts, and then check the ones using advertisement.

  <Arguments>
    config: The configuration dictionary.

  <Returns>
    A TCP socket to the host.
  """
  if "ip" in config and config["ip"]:
    host_ip = config["ip"]
  elif config["host"] in HOSTS:
    host_ip = HOSTS[config["host"]]
  else:
    ips = find_testbed(config["host"])
    if ips == ['']:
      raise Exception, "Failed to find host!"
    host_ip = ips[-1] # Use the last IP    

  try:
    socket = openconn(host_ip, PORT)
  except Exception,e:
    print "Error! Host IP:",host_ip,"Port:",PORT,"Reason:",str(e)
    raise 
  return socket

def send_mess(socket,message,digits=4):
  """
  <Purpose>
    Sends a message to the remote server, prefixing it with 'digits' number of digits,
    to indicate the length.
 
  <Arguments>
    socket: The socket to send on.
    message: The message to send
    digits: The number of digits to use. Defaults to 4.

  <Returns>
    Nothing.
  """
  # Prefix the message with a length indicator, then send the message
  length = len(message)
  length = str(length).rjust(digits,"0")
  mesg = length+message  
  while mesg != "":  
    sent = socket.send(mesg)
    mesg = mesg[sent:]

def get_bool_response(socket):
  """
  <Purpose>
    Gets a string response from the remote server and converts this to a bool True/False
  
  <Arguments>
    socket: The socket to read from.

  <Returns>
    True or False.
  """
  # Get response, 8 characters
  response = socket.recv(8)
  response = response.strip()
  
  if response == "True":
    return True
  else:
    return False

# Authenticates
def authenticate(socket, config):
  """
  <Purpose>
    Attempts to authenticate the current connection.

  <Arguments>
    socket: A TCP socket to the remote host.
    config: The configuration dictionary.

  <Returns>
    True if authenticated, False otherwise.
  """
  # Generate the auth string
  auth_str = config["user"] + ";" + config["pass"]
  
  # Send the string
  send_mess(socket,auth_str)

  # Return response
  return get_bool_response(socket)

# Creates a tar file of the needed data
def create_tar(config):
  """
  <Purpose>
    Creates a gzipped tarfile with all the files needed.

  <Arguments>
    config: The configuration dictionary. Checks the 'dir' directive.

  <Returns>
    The name of the tarfile.
  """
  name = "files."+str(config["host"])+"."+str(int(time.time()))+".tgz"
  tar = tarfile.open(name,"w:gz")
  tar.add(config["dir"],arcname="")
  tar.close()
  return name

# Uploads the tar file
def upload_tar(tarfilename, socket):
  """
  <Purpose>
    Uploads the tarfile. Prefixes the file with its MD5 hash so that the server can check its validity.

  <Arguments>
    tarfilename: The file name of the tarfile.
    socket: The socket to send it over.

  <Returns>
    True if the file had a hash match, False otherwise.
  """
  # Read in the tar file
  fileh = open(tarfilename,"rb")
  data = fileh.read()
  fileh.close()

  # Calculate the hash
  hash = hashlib.md5(data).hexdigest()

  # Send the hash and the data
  send_mess(socket, hash+data, 8)

  # Get the response
  return get_bool_response(socket)

CHUNKS = 512
# Prints the results
def dump_result(socket):
  """
  <Purpose>
    Once the remote test is started, we just read from the socket and dump to stdout.

  <Arguments>
    socket: The TCP socket to the remote server.

  <Returns>
    Nothing.
  """
  # Setup the interrupt handler
  signal.signal(signal.SIGINT,interrupt)
  try:
    while True:
      try:
        data = socket.recv(512)
        if data == "":
          break
        sys.stdout.write(data)
      except select.error:
        # This means we got a SIGINT...
        pass
  except Exception, e:
    print "[remotetest.py] Exception:",type(e),e
    pass
    
# When we catch a signal, send "cancel" to the remote server to stop the test  
def interrupt(signum, stack):
  """
  <Purpose>
    This is an interrupt handler. It will respond to SIGINT (Control-C), and react
    in an appropriate fashion. It will send 'cancel' to the remote server, which will kill
    the currently executing process. It will not terminate remotetest.py, but allow for a graceful termination.

  <Arguments>
   See signal.signal

  <Returns>
   Nothing
  """
  global socket
  socket.send("cancel")
  print "[remotetest.py] Sent interrupt to remote host!"

def main():
  """
  <Purpose>
    This is the main function. It will do the following:
    1) Parse the options
    2) If the options are bad, print usage and exit
    3) If --list or --hostinfo is specified, do the proper thing and then exit.
    4) Else we are connecting to a remote host. First create the tarfile
    5) Connect then Authenticate the connection, quit on failure.
    6) Upload the tarfile
    7) Upload the arguments
    8) Dump the results of the test.
    9) Close the socket and quit.
  """
  global socket

  # Parse the options
  options, args = getopt.getopt(sys.argv[1:], "", ["list","hostinfo=","user=","pass=","host=","dir=","args=","ip="])
  
  config = {"user":None,"pass":None,"host":None,"dir":None,"args":None,"ip":None}  
  for (flag, val) in options:
    if flag == "--user":
      config["user"] = val
    elif flag == "--pass":
      config["pass"] = val
    elif flag == "--host":
      config["host"] = val
    elif flag == "--dir":
      config["dir"] = val
    elif flag == "--args":
      config["args"] = val
    elif flag == "--ip":
      config["ip"] = val
    elif flag == "--list":
      # Find the available testbeds, print and exit
      hosts = find_testbeds()
      print "Available testbeds:",hosts
      exit()
    elif flag == "--hostinfo":
      # Get the IP's for the host
      ips = find_testbed(val)
      print "IP Addresses for:",val,ips
      exit()

  # Check for proper configuration 
  if not config["user"] or not config["pass"] or (not config["host"] and not config["ip"]) or not config["dir"] or not config["args"]:
     print "Bad Parameters!"
     print "Usage: python remotetest.py --list"
     print "Usage: python remotetest.py --hostinfo HOST"
     print "Usage: python remotetest.py --user USERNAME --pass PASSWORD --host HOST --dir TESTDIR [--ip IP] --args 'script'"
     print "Example: python remotetest.py --user seatttle --pass devel --host linux --dir test --args run_tests.py"
     exit()

  print "Configuration:",config 
  
  # Create a tar file, do first to avoid timeout
  print "Creating tar file..."
  tarfile = create_tar(config)
  print "Created:",tarfile

  # Connect to the proper host
  print "Connecting..."
  socket = connect_to_host(config) 

  # Authenticate
  print "Authenticating..."
  auth = authenticate(socket, config)
  if not auth:
    print "Authentication Failed!"
    os.remove(tarfile)
    exit()
  
  # Upload the tar file
  print "Uploading tar file..."
  status = upload_tar(tarfile,socket)
  print "Upload Status:",status
  
  # Remove the tar file
  print "Removing tar file:",tarfile
  os.remove(tarfile)
  if not status:
    exit()

  # Send the arguments
  print "Uploading arguments..."
  send_mess(socket, config["args"])

  # Setup an interrupt handler, inform the user 
  print "Setup interrupt handler on SIGINT to stop remote test."

  # Print the results
  print "Starting to dump result:"
  dump_result(socket)

  # Try to close the socket
  try:
    socket.close()
  except:
    pass

  print "Done! Exiting."

if __name__ == "__main__":
  main()
