#!/usr/bin/env python

import Rpi.GPIO as GPIO
from mfrc522 impot SimpleMFRC522

reader = SimpleMFRC522()

try:
  text = input('New data:')
  print("Now place you tag to write")
  reader.write(text)
  print("Written")
finally:
  GPIO.cleanup()
