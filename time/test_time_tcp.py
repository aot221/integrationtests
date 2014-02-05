"""
<Program Name>
  test_time_tcp.py

<Started>
  Jul 26, 2009

<Author>
  Eric Kimbrel

<Purpose>
  Send out emails if fewer than 5 timeservers are running
"""

import sys
import send_gmail
import integrationtestlib
import traceback
import time
import math

# use repy helper to bring in tcp_time.repy
import repyhelper

repyhelper.translate_and_import('tcp_time.repy')
repyhelper.translate_and_import('ntp_time.repy')

def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)


  notify_str = ''

  integrationtestlib.log("Starting test_time_tcp.py...")  

  # Whenever we fail to do tcp_time_updatetime, we add the exception string
  exception_string_list = []
  
  # get the time 5 times and make sure they are reasonably close
  test_start = getruntime()
  times = []
 
  # Keep a list of servers we connected to or tried to connect to for time.
  server_list = []

  # Connect to 5 servers and retrieve the time.
  for i in range (5):
    try:
      connected_server = tcp_time_updatetime(12345)
      current_time = time_gettime()
      times.append(current_time)
      server_list.append(connected_server)
      integrationtestlib.log("Calling time_gettime(). Retrieved time: " + str(current_time))
    except Exception,e:
      exception_string_list.append({'Server' : connected_server, 'Exception' : str(e), 'Traceback' : str(traceback.format_exc())})
      pass

  # Get the stop time 
  test_stop1 = getruntime()


  # Make sure that we don't fail too many times
  if len(times) < 4:  # more than one attempt failed
    notify_str += "failed to get ntp time via tcp at least twice in 5 attempts\n\n"
    notify_str += "Appending a list of all the exceptions returned and servers we attempted to connect to:\n\n"
    notify_str += str(exception_string_list)

  fail_test_str = ''

  # Find out the difference in time between the start time and end time of the test.
  diff = max(times) - min(times)
  test_diff = test_stop1 - test_start

  # If the time difference was more then 10 seconds then there is a problem.
  if math.fabs(diff - test_diff) > 10:  
    fail_test_str += ' WARNING large descrepancy between tcp times. \nThe difference between tcp_time diff and the actual test diff is: '+str(diff - test_diff)
    fail_test_str += "\n\nThe start time of test was: " + str(test_start) + ". The end time of test was: " + str(test_stop1)
    fail_test_str += "\n\nThe list of times returned by the tcp_server were: " + str(times)
    fail_test_str += "\n\nThe max time was: " + str(max(times)) + ". The min time was: " + str(min(times))
    fail_test_str += ". \n\nThe tcp diff time was: " + str(diff) + ". This time should have been less then: " + str(test_diff)
    fail_test_str += "\n\nThe servers we connected to are: " + str(server_list) 
    notify_str += fail_test_str
    integrationtestlib.log(fail_test_str)
    integrationtestlib.log("Local time diff: " + str(local_end_time - local_start_time))    

  # Now do an ntp time test
  try:
    ntp_time_updatetime(12345)
    ntp_t = time_gettime()
  except Exception,e:
    integrationtestlib.log("Failed to call ntp_time_updatetime(). Returned with exception: " +str(e))
    notify_str += "\nFailed to call ntp_time_updatetime(). Returned with exception: " +str(e)
  
  test_stop2 = getruntime()
  diff = ntp_t - max(times)
  if diff > (8 + test_stop2 - test_stop1):
    exceedby = diff - (test_stop2-test_stop1)
    integrationtestlib.log('WARING large descrepancy between ntp and tcp times')
    notify_str += ' WARNING large descrepancy between ntp and tcp time: '+str(exceedby)

  
  if notify_str != '':
    integrationtestlib.notify(notify_str, "test_time_tcp test failed")  
  else:
    integrationtestlib.log("Finished running test_time_tcp.py..... Test Passed")
  print "......................................................\n"

  


if __name__ == '__main__':
  main()
