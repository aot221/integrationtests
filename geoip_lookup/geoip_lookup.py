"""
<Program Name>
  geoip_lookup.py

<Started>
  October 15, 2012

<Author>
  Monzur Muhammad

<Purpose>
  Runs unit tests on geoip_client.repy and the geoip server

  The test will check if the server is up and running.
"""

import sys
import send_gmail
import repyhelper
import integrationtestlib

repyhelper.translate_and_import("geoip_client.repy")


SERVER_DOWN = 1
INCORRECT_ASSERTION = 2



def main():
  """
  <Purpose>
    This is the main launching point for the integration tests.
    We check both our servers to ensure that both geoip servers
    are up and running.
  """

  # List of all the geoip servers.
  geoip_server_list = ['http://betaseattleclearinghouse.poly.edu:12679', 'http://geoip.cs.washington.edu:12679']

  # Keep track of stats.
  servers_down = []
  servers_running_properly = []
  servers_with_bad_response = []


  # Initialize the integration test lib.
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)



  # Contact each server to ensure they are running properly.
  for server in geoip_server_list:
    success, error_type, error_str = test_server(server)

    if success:
      servers_running_properly.append(server)
    else:
      if error_type == INCORRECT_ASSERTION:
        # If we got the wrong answer, we note what the error was.
        servers_with_bad_response.append((server, error_str))
      elif error_type == SERVER_DOWN:
        servers_down.append((server, error_str))

  # Initialize the email text and subject.
  email_subject = ""
  email_text = ""


  # If all the servers are not running properly we send out emails.
  if len(servers_running_properly) != len(geoip_server_list):
    # If all servers are down, then we are in trouble.
    if len(servers_running_properly) == 0:
      email_subject = "CRITICAL: All GeoIP servers are down!"
      email_text = "CRITICAL: All GeoIP servers are down or are not running properly.\n\n"
      
    # Only some servers are not functioning properly.
    else:
      email_subject = "WARNING: Some GeoIP servers are down or are not running properly."
      email_text = "Not all the GeoIP servers are running properly!\n\n"
      email_text += "Servers that are up and running properly:\n"
      
      for server_name in servers_running_properly:
        email_text += "\t%s\n" % server_name

    # If servers are unresponseive.
    if len(servers_down) > 0:
      email_text += "Servers that are down:\n"
    
      for (server_name, server_error) in servers_down:
        email_text += "\t%s, Error: %s\n" % (server_name, server_error)
 
    # If servers are giving bad response.
    if len(servers_with_bad_response) > 0 :
      email_text += "Servers with bad response:\n"
    
      for (server_name, server_error) in servers_with_bad_response:
        email_text += "\t%s, Error: %s\n" % (server_name, server_error)
     
    
    # Send out the notification email.
    integrationtestlib.notify(email_text, email_subject)

  else:
    email_text += "Servers that are up and running properly:\n"

    for server_name in servers_running_properly:
      email_text += "\t%s\n" % server_name    

  integrationtestlib.log(email_text)


  

def test_server(server_url):
  """
  <Purpose>
    Given an url, try to do GeoIP lookup to ensure that the server
    is running properly and giving accurate results.

  <Argument>
    server_url - the url of the geoip server.

  <Exceptions>
    None

  <Return>
    Boolean on whether we were able to contact the geoip server as well as the error.
  """

  geoip_init_client([server_url])

  try:
    # Test geoip_record_by_name method by verifying location info of google.com
    location_dict = geoip_record_by_name('poly.edu')
    expected_result = {'area_code': 718, 'city': 'Brooklyn', 'country_code': 'US', 'country_code3': 'USA', 'country_name': 'United States', 'dma_code': 501, 'latitude': 40.694400000000002, 'longitude': -73.990600000000001, 'postal_code': '11201', 'region_name': 'NY'}

    assert(expected_result['country_name'] == location_dict['country_name'])
    assert(expected_result['city'] == location_dict['city'])
    assert(expected_result['area_code'] == location_dict['area_code'])
    assert(expected_result['region_name'] == location_dict['region_name'])
    assert(expected_result['postal_code'] == location_dict['postal_code'])

    # Test geoip_location_str method
    assert(geoip_location_str(location_dict) == "Brooklyn, NY, United States")
  
    # Test geoip_record_by_name method by verifying location info of
    # 128.208.3.200 (cs.washington.edu)
    expected_result = {'city': 'Seattle', 'region_name': 'WA', 'area_code': 206, 'longitude': -122.2919, 'country_code3': 'USA', 'country_name': 'United States', 'postal_code': '98105', 'dma_code': 819, 'country_code': 'US', 'latitude': 47.660599999999988}
    location_dict = geoip_record_by_addr('128.208.3.200')
    
    assert(expected_result['country_name'] == location_dict['country_name'])
    assert(expected_result['city'] == location_dict['city'])
    assert(expected_result['area_code'] == location_dict['area_code'])
    assert(expected_result['region_name'] == location_dict['region_name'])
    assert(expected_result['postal_code'] == location_dict['postal_code'])


    # Test geoip_location_str method
    assert(geoip_location_str(location_dict) == "Seattle, WA, United States")

    return (True, None, None)
  except AssertionError, err:
    return (False, INCORRECT_ASSERTION, str(err))
  except Exception, err:
    return (False, SERVER_DOWN, str(err))  



if __name__ == '__main__':
  main()

