
from repyportability import *
import hashlib
import getopt
import tarfile
import time
import sys
import os
import repyhelper

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
  # Prefix the message with a length indicator, then send the message
  length = len(message)
  length = str(length).rjust(digits,"0")
  mesg = length+message  
  while mesg != "":  
    sent = socket.send(mesg)
    mesg = mesg[sent:]

def get_bool_response(socket):
  # Get response, 8 characters
  response = socket.recv(8)
  response = response.strip()
  
  if response == "True":
    return True
  else:
    return False

# Authenticates
def authenticate(socket, config):
  # Generate the auth string
  auth_str = config["user"] + ";" + config["pass"]
  
  # Send the string
  send_mess(socket,auth_str)

  # Return response
  return get_bool_response(socket)

# Creates a tar file of the needed data
def create_tar(config):
  name = "files."+str(int(time.time()))+".tar"
  tar = tarfile.open(name,"w")
  tar.add(config["dir"],arcname="")
  tar.close()
  return name

# Uploads the tar file
def upload_tar(tarfilename, socket):
  # Read in the tar file
  fileh = open(tarfilename)
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
  try:
    while True:
      data = socket.recv(512)
      if data == "":
        break
      sys.stdout.write(data)
  except:
    pass
    

def main():
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
  # Connect to the proper host
  print "Connecting..."
  socket = connect_to_host(config) 

  # Authenticate
  print "Authenticating..."
  auth = authenticate(socket, config)
  if not auth:
    print "Authentication Failed!"
    exit()
  
  # Create a tar file
  print "Creating tar file..."
  tarfile = create_tar(config)
  print "Created:",tarfile

  # Upload the tar file
  print "Uploading tar file..."
  status = upload_tar(tarfile,socket)
  print "Upload Status:",status
  if not status:
    exit()

  # Send the arguments
  print "Uploading arguments..."
  send_mess(socket, config["args"])

  # Print the results
  print "Starting to dump result:"
  dump_result(socket)

  # Try to close the socket
  try:
    socket.close()
  except:
    pass

  # Remove the tar file
  print "Removing tar file:",tarfile
  os.remove(tarfile)

  print "Done! Exiting."

if __name__ == "__main__":
  main()
