import os
import math
import time
import RPi.GPIO as GPIO
import base64
from time import sleep
import busio
import board
from Adafruit_IO import Client, Feed, RequestError
import numpy as np
import pygame
from scipy.interpolate import griddata
import subprocess
from colour import Color
import adafruit_amg88xx

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)

i2c_bus = busio.I2C(board.SCL, board.SDA)

ADAFRUIT_IO_KEY = 'YOUR_ADAFRUIT_IO_KEY'
ADAFRUIT_IO_USERNAME = 'YOUR_ADAFRUIT_IO_USERNAME'
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
picam_feed = aio.feeds('YOUR_IO_IMAGE_FEED') # For uploading snapshots to dashboard
tempmin = aio.feeds('YOUR_IO_MIN_TEMP_FEED') # For downloading from dashboard Min slider
tempmax = aio.feeds('YOUR_IO_MIN_TEMP_FEED') # For downloading from dashboard Max slider

tempmin_read = aio.receive(tempmin.key)
tempmax_read = aio.receive(tempmax.key)

print("Minimum: " + tempmin_read.value)
print("Maximum: " + tempmax_read.value)

#low range of the sensor (this will be blue on the screen)
MINTEMP = float(tempmin_read.value)

#high range of the sensor (this will be red on the screen)
MAXTEMP = float(tempmax_read.value)

#how many color values we can have
COLORDEPTH = 1024

os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()

#initialize the sensor
sensor = adafruit_amg88xx.AMG88XX(i2c_bus)

# pylint: disable=invalid-slice-index
points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]
# pylint: enable=invalid-slice-index

#sensor is an 8x8 grid so lets do a square
height = 240
width = 240

#the list of colors we can choose from
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

#create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

displayPixelWidth = width / 30
displayPixelHeight = height / 30

lcd = pygame.display.set_mode((width, height))

lcd.fill((255, 0, 0))

pygame.display.update()
pygame.mouse.set_visible(False)

lcd.fill((0, 0, 0))
pygame.display.update()

def buzz():

    GPIO.output(16,True)
    sleep(0.4)
    GPIO.output(16,False)
    sleep(0.1)
    GPIO.output(16,True)
    sleep(0.4)
    GPIO.output(16,False)

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#let the sensor initialize
time.sleep(.1)

running = True

while running:

    #read the pixels
    pixels = []
    for row in sensor.pixels:
        pixels = pixels + row
    pixels = [map_value(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]

    icon = 'doctor'
    #perform interpolation
    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')

    #draw everything
    for ix, row in enumerate(bicubic):
        for jx, pixel in enumerate(row):
            pygame.draw.rect(lcd, colors[constrain(int(pixel), 0, COLORDEPTH- 1)],
                             (displayPixelHeight * ix, displayPixelWidth * jx,
                              displayPixelHeight, displayPixelWidth))

    pygame.display.update()
    if (GPIO.input(23) ==0):
       
        print ("Fever")
        buzz()
        GPIO.output(12,True)
        sleep(1)
        GPIO.output(12,False)
        running = False
        pygame.quit()
        subprocess.Popen(["python3", "/home/pi/FeverChill/menu.py", icon]) 
        exit()

    elif ( GPIO.input(24) ==0):
        
        print ("Chill")
        buzz()
        GPIO.output(12,True)
        sleep(1)
        GPIO.output(12,False)
        running = False
        pygame.quit()
        subprocess.Popen(["python3", "/home/pi/FeverChill/menu.py", icon]) 
        exit()

    elif ( GPIO.input(26) ==0):

        print ("Capture")
        buzz()
        GPIO.output(12,True)
        sleep(1)
        pygame.image.save(lcd, "/home/pi/FeverChill/thermal.jpg")
        GPIO.output(12,False)
        with open("/home/pi/FeverChill/thermal.jpg", "rb") as imageFile:
            image = base64.b64encode(imageFile.read())
            # encode the b64 bytearray as a string for adafruit-io
            image_string = image.decode("utf-8")
            try:
              aio.send(picam_feed.key, image_string)
              print('Picture sent to Adafruit IO')
              buzz()
            except:
              print('Sending to Adafruit IO Failed...')

    else:
        sleep(.1)
