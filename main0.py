# COPYRIGHT Stefan Leung 2023

# setup imports
import pygame
import pygame_widgets
from pygame_widgets.button import Button
import sys
import time
from datetime import datetime
import random
import logging
import math

# Setup logging file
logging.basicConfig(filename=f'logs/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log', encoding='utf-8', level=logging.DEBUG)

# define display width and height
display_width = 1600
display_height = 1200
logging.debug(f'display width: {display_width}, display height: {display_height}')

# define colors
red = (255, 0, 0)
green = (0, 155, 0)
blue = (0, 0, 255)
cyan = (0, 255, 255)
black = (0, 0, 0)
white = (255, 255, 255)

# Set up game
logging.info("Initiating game...")
pygame.init()
screen = pygame.display.set_mode((display_width, display_height))

# Set up player class
class player_class:
    def __init__(self, x, y, width, height, speed=0, dir=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.dir = dir

    def move(self):
        self.x += self.speed * math.sin(math.radians(self.dir+90))
        self.y += self.speed * math.cos(math.radians(self.dir+90))

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(self.x, self.y, self.width, self.height))

# Create player
player = player_class(350, 250, 120, 50)

# Load images
cars_folder = ['red_car']
cars = {}
for i in cars_folder:
    cars[i] = {}
    cars[i]['straight'] = pygame.transform.rotate(pygame.image.load(f'img/{i}/straight.png'), 90)
    cars[i]['right'] = pygame.transform.rotate(pygame.image.load(f'img/{i}/right.png'), 90)
    cars[i]['left'] = pygame.transform.rotate(pygame.image.load(f'img/{i}/left.png'), 90)
current_car = cars['red_car']['straight']
logging.debug(f'Car images dict: {cars}')

monza_img = pygame.image.load('img/monza.png')
monza_img = pygame.transform.scale(monza_img, (997*2, 561*2))

# Image rotation script (copied from https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame - Rabbid76)
def blitRotate(surf, image, pos, originPos, angle):

    # offset from pivot to center
    image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1]-originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    
    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)
  
    # draw rectangle around the image
    pygame.draw.rect(surf, (255, 0, 0), (*rotated_image_rect.topleft, *rotated_image.get_size()),2)

# Speed multiplier
spd_multi = 900000

# Turning logic function
min_turn_speed = 0.2
turning_function = lambda: 0.00000035*spd_multi/(player.speed/7 if player.speed > min_turn_speed else min_turn_speed)

# Main game loop
logging.info("Launching game...")
running = True
while running:
    # Draw sprites
    screen.fill((50, 50, 50))
    blitRotate(screen, monza_img, (display_width/2+player.x,display_height/2+player.y), (player.x, player.y), player.dir)
    screen.blit(current_car, (display_width/2,display_height/2))

    # Quit script, Log player info script
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            logging.info("Shutting down...")
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                logging.info(f'Keypressed: {event.key}')
                logging.info(f'Player: x={player.x}, y={player.y}, dir={player.dir}, speed={player.speed}')
    
    # Speed logic
    keys = pygame.key.get_pressed()
    old_dir = player.dir
    if keys[pygame.K_UP]:
        player.speed += (0.00004*spd_multi) if player.speed <= (4*spd_multi) else 0
    elif player.speed > 0:
        player.speed -= (0.00001*spd_multi) if player.speed > (0.0001*spd_multi) else player.speed
    if keys[pygame.K_DOWN] and player.speed > 0:
        player.speed -= (0.00008*spd_multi)
    elif player.speed < 0:
        player.speed += (0.00001*spd_multi) if player.speed < (0.0001*spd_multi) else abs(player.speed)
    player.speed *= -1

    # Turning logic
    if keys[pygame.K_LEFT] and player.speed != 0:
        player.dir += turning_function() if player.speed > 0 else -turning_function()
    if keys[pygame.K_RIGHT] and player.speed != 0:
        player.dir -= turning_function() if player.speed > 0 else -turning_function()
    player.move()

    # Wheel direction logic
    if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]: current_car = cars['red_car']['straight']
    elif keys[pygame.K_LEFT]: current_car = cars['red_car']['left']
    elif keys[pygame.K_RIGHT]: current_car = cars['red_car']['right']
    else: current_car = cars['red_car']['straight']
    
    # Calculate player's direction
    if old_dir != player.dir:
        if player.dir >= 360:
            player.dir -= 360
        elif player.dir < 0:
            player.dir += 360

    pygame.display.flip()

pygame.quit()