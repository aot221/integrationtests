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

  #add Eric Kimbrel to the email notify list
  integrationtestlib.notify_list.append("lekimbrel@gmail.com")
    
  integrationtestlib.log("Starting test_time_tcp.py...")  
  
  # get the time 5 times and make sure they are reasonably close
  test_start = getruntime()
  times = []
  for i in range (5):
    try:
      tcp_time_updatetime(12345)
      times.append(time_gettime())
    except Exception,e:
      pass
  test_stop1 = getruntime()

  
  if len(times) < 4:  # more than one attempt failed
    fail_test('failed to get ntp time via tcp at least twice in 5 attempts')

  diff = max(times) - min(times)
  if diff > (test_stop1 - test_start):  
    integrationtestlib.log('WARNING large descrepancy between times: '+str(diff))
    fail_test('WARNING large descrepancy between times: '+str(diff))
    
  
  try:
    ntp_time_updatetime(12345)
    ntp_t = time_gettime()
  except Exception,e:
    fail_test(str(e))
  
  test_stop2 = getruntime()

  if ntp_t > (1 + test_stop2 - test_stop1)+max(times):
    integrationtestlib.log('WARING large descrepancy between ntp and tcp times')
    fail_test('WARNING large descrepancy between times: '+str(diff))

  integrationtestlib.log("Finished running test_time_tcp.py..... Test Passed")
  print "......................................................\n"



def fail_test(err_str):
  # notify uses that this test has failed
  integrationtestlib.notify('WARNING: test_time_tcp.py  FAILED, only '+err_str, "test_time_tcp test failed")
  sys.exit()


if __name__ == '__main__':
  main()
