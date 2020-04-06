#!/usr/bin/env python3

import os
import pygame
import RPi.GPIO as GPIO
from time import sleep
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)

os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()

SIZE = WIDTH, HEIGHT = 240, 240
BACKGROUND_COLOR = pygame.Color('black')
FPS = 30

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()

pygame.mouse.set_visible(0)

def buzz():

    GPIO.output(16,True)
    sleep(0.4)
    GPIO.output(16,False)
    sleep(0.1)
    GPIO.output(16,True)
    sleep(0.4)
    GPIO.output(16,False)


def load_images(path):
    """
    Loads all images in directory. The directory must only contain images.

    Args:
        path: The relative or absolute path to the directory to load images from.

    Returns:
        List of images.
    """
    images = []
    for file_name in os.listdir(path):
        image = pygame.image.load(path + os.sep + file_name).convert()
        images.append(image)
    return images


class AnimatedSprite(pygame.sprite.Sprite):

    def __init__(self, position, images):
        """
        Animated sprite object.

        Args:
            position: x, y coordinate on the screen to place the AnimatedSprite.
            images: Images to use in the animation.
        """
        super(AnimatedSprite, self).__init__()

        size = (240, 240)  # This should match the size of the images.

        self.rect = pygame.Rect(position, size)
        self.images = images
        self.images_right = images
        self.images_left = [pygame.transform.flip(image, True, False) for image in images]  # Flipping every image.
        self.index = 0
        self.image = images[self.index]  # 'image' is the current image of the animation.

        self.velocity = pygame.math.Vector2(0, 0)

        self.animation_time = 1
        self.current_time = 0

        self.animation_frames = 6
        self.current_frame = 0

    def update_time_dependent(self, dt):
        """
        Updates the image of Sprite approximately every 0.1 second.

        Args:
            dt: Time elapsed between each frame.
        """
        if self.velocity.x > 0:  # Use the right images if sprite is moving right.
            self.images = self.images_right
        elif self.velocity.x < 0:
            self.images = self.images_left

        self.current_time += dt
        if self.current_time >= self.animation_time:
            self.current_time = 0
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]

        self.rect.move_ip(*self.velocity)

    def update_frame_dependent(self):
        """
        Updates the image of Sprite every 6 frame (approximately every 0.1 second if frame rate is 60).
        """
        if self.velocity.x > 0:  # Use the right images if sprite is moving right.
            self.images = self.images_right
        elif self.velocity.x < 0:
            self.images = self.images_left

        self.current_frame += 1
        if self.current_frame >= self.animation_frames:
            self.current_frame = 0
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]

        self.rect.move_ip(*self.velocity)

    def update(self, dt):
        """This is the method that's being called when 'all_sprites.update(dt)' is called."""
        # Switch between the two update methods by commenting/uncommenting.
        self.update_time_dependent(dt)
        # self.update_frame_dependent()


def main():
    images = load_images(path='/home/pi/FeverChill/anim/')  # Make sure to provide the relative or full path to the images directory.
    player = AnimatedSprite(position=(0, 0), images=images)
    all_sprites = pygame.sprite.Group(player)  # Creates a sprite group and adds 'player' to it.

    icon = 'doctor'
    running = True
    while running:

        dt = clock.tick(FPS) / 1000  # Amount of seconds between each loop.
               
        if (GPIO.input(23) ==0):
       
            print ("Fever")
            GPIO.output(12,True)
            buzz()
            sleep(1)
            GPIO.output(12,False)
            running = False
            pygame.quit()
            subprocess.Popen(["python3", "/home/pi/FeverChill/fever.py", icon]) 
            exit()
            
        elif ( GPIO.input(24) ==0):
        
            print ("Chill")
            GPIO.output(12,True)
            buzz()
            sleep(1)
            GPIO.output(12,False)
            running = False
            pygame.quit()
            subprocess.Popen(["python3", "/home/pi/FeverChill/chill.py", icon])
            exit()
        else:
            sleep(.2)

        all_sprites.update(dt)  # Calls the 'update' method on all sprites in the list (currently just the player).

        screen.fill(BACKGROUND_COLOR)
        all_sprites.draw(screen)
        pygame.display.update()


if __name__ == '__main__':
    main()
