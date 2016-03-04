#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import required modules
import time
import RPi.GPIO as GPIO

# set GPIO pin with connected button
GPIOPin = 22 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
Counter=0;
# main function
def main():
  value = 0
  while True:
    # increment value if button is pressed
    if not GPIO.input(GPIOPin):
      value += 0.5
    if value > 0:
      if value >= 3:
        print "lang"
      elif GPIO.input(GPIOPin):
        print "kurz"
    # wait 500ms
    time.sleep(0.5)
  return 0

if __name__ == '__main__':
  # use GPIO pin numbering convention
  GPIO.setmode(GPIO.BCM)

  # set up GPIO pin for input
  GPIO.setup(GPIOPin, GPIO.IN)

  # call main function
  try:
    main()
  finally:
    GPIO.cleanup()
