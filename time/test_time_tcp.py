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



def main():
  # initialize the gmail module
  success,explanation_str = send_gmail.init_gmail()
  if not success:
    integrationtestlib.log(explanation_str)
    sys.exit(0)

  # use repy helper to bring in advertise.repy
  repyhelper.translate_and_import('tcp_time.repy')
  
  # get the time 5 times and make sure they are reasonably close
  test_start = getruntime()
  times = []
  for i in range (5):
    try:
      time_updatetime(12345)
      times.append(time_gettime())
    except Exception,e:
      pass
  test_stop = getruntime()

  
  if len(times) < 4:  # more than one attempt failed
    test_fail('failed to get ntp time via tcp at least twice in 5 attempts')

  diff = max(times) - min(times)
  if diff > (test_stop - test_start):  
    print 'WARNING large descrepancy between times: '+str(diff)
    fail_test('WARNING large descrepancy between times: '+str(diff))
    
  
  # now bring in ntp_time.repy for a comparison
  repyhelper.translate_and_import('ntp_time.repy')
  try:
    ntp_time_updatetime(12345)
    ntp_t = time_gettime()
  except Exception,e:
    fail_test(str(e))

  if ntp_t > 2+max(times):
    print 'WARING large descrepancy between ntp and tcp times'
    fail_test('WARNING large descrepancy between times: '+str(diff))




def fail_test(err_str):
  # notify uses that this test has failed
  integrationtestlib.notify('WARNING: test_time_tcp.py  FAILED, only '+err_str
  sys.exit()


if __name__ == '__main__':
  main()
