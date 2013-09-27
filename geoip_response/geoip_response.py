"""
<Program Name>
  geoip_failure_test.py

<Purpose>
  This is a monitoring script to test how many times the geoip server is
  failing to respond in a given amount of time. It will send an email if
  an server did not respond.

<Side Effects>
  Creates a file named geoip_failuer_test.out, to log all the valid responses. 
"""
import repyhelper
import time
import integrationtestlib

repyhelper.translate_and_import('geoip_client.repy')

TEST_IP = "128.238.66.181"

def sendmail(start_time, err_msg, elapsed_time, err_interval, counter):
  # Recipient email to the send the notification...
  integrationtestlib.notify_list = ['ak4282@students.poly.edu',\
   'llaw02@students.poly.edu', 'jcappos@poly.edu']

  subject = "Error caught while testing GeoIP."
  
  message = "Monitoring script started at: " + str(time.ctime(start_time))
  message += "\n Error occurred " + str(counter) + " times, in the last " +\
   str(elapsed_time/60.0) + " mins."
  message += "\n Time since the last error: " + str(err_interval/60.0)  
  message += "\n Error: " + str(err_msg) + "\n\n"

  integrationtestlib.notify(message, subject)


def main():
  # Save the time when the script started to monitor...
  start_time = time.time()

  geoip_init_client()

  # Keep a tab on how many times the geoip server is failing to respond. 
  counter = 0
  err_time = 0.0

  # Run the script for 18 hours and then quit...
  while (time.time() - start_time) <= (18*60*60):
    try:
      # Query the location of an IP and check whether the server is failing
      # to respond or not...
      ret = geoip_record_by_addr(TEST_IP)
    
      # log the successful results into a file...
      open("geoip_failure_test.out", "a").write(str(ret) + '\n')
      
    except Exception, err:
      counter += 1 # count for number of times the server has failed...
      prev_err_time = err_time # time between the last two errors...
      err_time = time.time() # Get the time when the server failed to respond.

      # Time to send the mail, (err_time-start_time) gives the duration of 
      # time to see how many times the server has failed in that interval.
      sendmail(start_time, err, err_time - start_time,
        err_time - prev_err_time, counter)
      print "a mail was sent"
    finally:
      # whatever the result is, wait for 15 mins and retry...
      time.sleep(15*60)

if __name__ == '__main__':
  main()
