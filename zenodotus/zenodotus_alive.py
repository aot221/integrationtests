"""
<Filename>
  zenodotus_alive.py

<Purpose>
  This is an integration test script that will look up zenodotus via
  DNS to ensure that it points to blackbox.

"""
import integrationtestlib
import send_gmail
import os
import sys
import repyhelper

repyhelper.translate_and_import('advertise.repy')
repyhelper.translate_and_import('random.repy')
repyhelper.translate_and_import('rsa.repy')
repyhelper.translate_and_import('sha.repy')


zenodotus_servername = "zenodotus.poly.edu"
zenodotus_ipaddr = '128.238.63.50'


def _dns_mapping_exists(name, ip_address):
  for line in os.popen('dig @8.8.8.8 ' + name, 'r').readlines():
    # Can't do direct comparison between dig's output and hardcoded string
    # TTL value changes on each call.  Instead, check if any of the lines
    # contain the entry for blackbox.
    if name + '.' in line.split() and ip_address in line.split():
      return True
  return False


def _generate_random_ip_address():
  octets = []
  for octet in xrange(4):
    octets.append(str(random_int_below(256)))
  return '.'.join(octets)


def main():
  # Initialize the gmail setup.
  success, explanation_str = send_gmail.init_gmail()

  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  print "Beginning query."
  success = True

  try:
    # Query zenodotus
    if not _dns_mapping_exists(zenodotus_servername, zenodotus_ipaddr):
      print "Zenodotus failed to respond properly!"
      # Query is invalid!
      success = False
      integrationtestlib.notify("Error: Zenodotus has failed to correctly respond; the machine has likely been rebooted. Please restart the zenodotus server on zenodotus@blackbox. This report will be re-sent hourly while the problem persists.", "Cron: Zenodotus failure")

    # Check that advertised values work
    # Map an entirely random IP to a random DNS name. The mapped IP does
    # not have to actually exist (but should still be valid).
    random_ip_address = _generate_random_ip_address()

    random_publickey = rsa_gen_pubpriv_keys(1024)[0]
    random_publickey_string = rsa_publickey_to_string(random_publickey)
    random_subdomain = "test-" + sha_hexhash(random_publickey_string)
    random_dns_entry = random_subdomain + '.' + zenodotus_servername

    print "Announcing", random_dns_entry, random_ip_address
    advertise_announce(random_dns_entry, random_ip_address, 60)

    if not _dns_mapping_exists(random_dns_entry, random_ip_address):
      print "Zenodotus failed to respond properly to advertised subdomain!"
      # Query is invalid!
      success = False
      integrationtestlib.notify("Error: Zenodotus has failed to correctly respond to an advertised subdomain; there might be something wrong with the advertise server. This report will be re-sent hourly while the problem persists.", "Cron: Zenodotus failure")



  except Exception, e:
    print "Unknown error!"
    print str(e)
    success = False
    integrationtestlib.notify("Error: Zenodotus seems to be down! Error data: " + str(e), "Cron: Zenodotus failure")

  if success:
    print "Query was successful."

if __name__ == "__main__":
  main()
