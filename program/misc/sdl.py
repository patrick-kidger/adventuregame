"""Basically just a pygame wrapper, to make it easier to change it out later if need be."""

import pygame
import pygame.ftfont
import pygame.display
import pygame.event

# Initialise the pygame modules
pygame.ftfont.init()
pygame.display.init()


# Top-level pygame imports
Surface = pygame.Surface

# And top-level keycodes
QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN
K_LSHIFT = pygame.K_LSHIFT
K_RSHIFT = pygame.K_RSHIFT
K_BACKSPACE = pygame.K_BACKSPACE
K_RETURN = pygame.K_RETURN
K_KP_ENTER = pygame.K_KP_ENTER
K_ESCAPE = pygame.K_ESCAPE
K_BACKSLASH = pygame.K_BACKSLASH


# Emulate its modules
class ftfont(object):
    SysFont = pygame.ftfont.SysFont


class display(object):
    set_mode = pygame.display.set_mode
    set_caption = pygame.display.set_caption
    update = pygame.display.update


class event(object):
    clear = pygame.event.clear
    wait = pygame.event.wait


class image(object):
    load = pygame.image.load


# Custom stuff
K_SHIFT = (K_LSHIFT, K_RSHIFT)
K_ENTER = (K_KP_ENTER, K_RETURN)