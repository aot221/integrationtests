"""
<Program>
  test_lookup_node_states.py

<Purpose>
  use advertise.repy to do a lookup for nodes in the four
  differe states: acceptdonation, canonical, onepercentmanyevents
  and movingtoonepercentmanyevents. And send out notifications
  if the number of nodes in each state is not what is expected.

<Started> 
  August 5, 2009

<Author>
  Monzur Muhammad
  monzum@cs.washington.edu
"""

import integrationtestlib
import send_gmail

import repyhelper
repyhelper.translate_and_import('rsa.repy')
repyhelper.translate_and_import('advertise.repy')

#get all public keys for different states from file
onepercent_manyevent_pubkey = rsa_file_to_publickey("/home/integrationtester/cron_tests/lookup_node_states/onepercentmanyevents.publickey")
canonicalpublickey = rsa_file_to_publickey("/home/integrationtester/cron_tests/lookup_node_states/canonical.publickey")
acceptdonationpublickey = rsa_file_to_publickey("/home/integrationtester/cron_tests/lookup_node_states/acceptdonation.publickey")
movingtoonepercentpublickey = rsa_file_to_publickey("/home/integrationtester/cron_tests/lookup_node_states/movingtoonepercent.publickey")

important_node_states = [('onepercent_manyevent', onepercent_manyevent_pubkey), ('canonical', canonicalpublickey), ('acceptdonation', acceptdonationpublickey), ('movingtoonepercent', movingtoonepercentpublickey)] 


def check_nodes(server_lookup_type):
  """
  <Purpse>
    Check for nodes that are in the central server and find the nodes in differen
    states.

  <Arguments>
    server_lookup_type - either central or opendht

  <Exception>
    AdvertiseLookup - raised if advertise_lookup gives an error.

  <Side Effects>
    None

  <Return>
    None 
  """
  #counter used to count the total number of nodes
  total_nodes = 0
  node_result = {}
  integrationtestlib.log("Starting advertise_lookup() using only "+server_lookup_type+" lookup type")

  print server_lookup_type 
  #go through all the possible node states and do an advertise lookup
  for node_state_name, node_state_pubkey in important_node_states:
    integrationtestlib.log("Printing "+node_state_name+" nodes:")

    #retrieve node list from advertise_lookup(
    try:
      node_list = advertise_lookup(node_state_pubkey, maxvals = 10*1024*1024, lookuptype=[server_lookup_type])
    except:
      raise AdvertiseLookup, "advertise_lookup() failed when looking up key: "+ node_state_pubkey + " for "+server_lookup_type

    #keep track of total nodes
    total_nodes+=len(node_list)
    
    node_result[node_state_name] = len(node_list)

    #logg all the node lookup info
    for node in node_list:
      print node

  node_result['Total nodes'] = total_nodes
  return node_result   




def main():
  """
  <Purpose>
    Call check_nodes with the two different servers: opendht and central. Retrieve the result 
    and then notify developers if result is unusual

  <Exceptions>
    None

  <Side Effects>
    May send out an email or notify on irc.

  <Return>
    None
  """
  #setup the gmail for sending notification
  success,explanation_str = send_gmail.init_gmail()

  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  notification_subject = "test_lookup_node_states() failed"

  max_acceptdonation_nodes = 50 
  max_canonical_nodes = 50 
  max_movingtoonepercent = 20
  min_onepercentmanyevents_nodes = 300 

  central_results = check_nodes('central')
  integrationtestlib.log("Lookup results for central: "+ str(central_results))

  #check to see if any of the results is not normal, and send notifications accordingly
  #also send a message to irc.  
  if central_results['acceptdonation'] > max_acceptdonation_nodes:
    message="Too many nodes in acceptdonation state: "+str(central_results['acceptdonation'])+"\nResults from 'central' server:\n"+str(central_results)
    print message
    integrationtestlib.notify(message, notification_subject)

  elif central_results['canonical'] > max_canonical_nodes:
    message="Too many nodes in canonical state: "+str(central_results['canonical'])+"\nResults from 'central' server:\n"+str(central_results)
    print message
    integrationtestlib.notify(message, notification_subject)

  elif central_results['onepercent_manyevent'] < min_onepercentmanyevents_nodes:
    message="Too few nodes in onepercentmanyevents state: "+str(central_results['onepercent_manyevent'])+"\nResults from 'central' server:\n"+str(central_results)
    print message
    integrationtestlib.notify(message, notification_subject)

  opendht_results = check_nodes('opendht')

  print opendht_results  
   

if __name__ == "__main__":
  main()







#exception raised if AdvertiseLookup fails somehow
class AdvertiseLookup(Exception):
  pass
