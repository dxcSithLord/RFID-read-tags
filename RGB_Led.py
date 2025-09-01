#libraries
from  gpiozero import RGBLED
from colorzero import Color
from time import sleep
led = RGBLED(12, 13, 19)

try:
  while True:
    led.off()
    sleep(1) #1second
    led.color = Color("white")
    sleep(1)
    led.color = Color("red")
    sleep(1)
    led.color = Color("green")
    sleep(1)
    led.color = Color("blue")
    sleep(1)
    led.color = Color("yellow")
    sleep(1)
    led.color = Color("purple")
    sleep(1)
    led.color = Color("lightblue")
    sleep(1)

finally:
    led.off()
