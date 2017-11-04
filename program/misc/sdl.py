"""Basically just a pygame wrapper, to make it easier to change it out later if need be."""

import pygame
import pygame.ftfont
import pygame.display
import pygame.event


import program.misc.exceptions as exceptions

# Initialise the pygame modules
pygame.ftfont.init()
pygame.display.init()
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])


# Top-level pygame imports
class Surface(pygame.Surface):
    def blit(self, source, dest=(0, 0), area=None, special_flags=0):  # Added default argument to dest
        return super(Surface, self).blit(source, dest, area, special_flags)

    def point_within(self, pos):
        offset = self.get_offset()
        rect = self.get_rect(left=offset[0], top=offset[1])
        return rect.collidepoint(pos)


Rect = pygame.Rect

# Event types
QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
# And top-level keycodes
K_LSHIFT = pygame.K_LSHIFT
K_RSHIFT = pygame.K_RSHIFT
K_BACKSPACE = pygame.K_BACKSPACE
K_RETURN = pygame.K_RETURN
K_KP_ENTER = pygame.K_KP_ENTER
K_ESCAPE = pygame.K_ESCAPE
K_BACKSLASH = pygame.K_BACKSLASH
K_SLASH = pygame.K_SLASH


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
    get = pygame.event.get
    poll = pygame.event.poll


class image(object):
    load = pygame.image.load


# Custom stuff
K_SHIFT = (K_LSHIFT, K_RSHIFT)
K_ENTER = (K_KP_ENTER, K_RETURN)


def event_stream(single_event=False, discard_old=True):
    """A generator providing a stream of events as inputs.

    If single_event is True, then it will instead just return a single event, or None if there is no event in the queue.
    if discard_old is also True, then it will discard all the other events.
    """
    def _event_stream(events):
        for event_ in events:
            if event_.type == QUIT:
                raise exceptions.CloseException()
            elif event_.type == KEYDOWN:
                if event_.key in K_SHIFT:
                    continue  # The modified key will be picked up on the next keystroke
            yield event_

    if single_event:
        events = (event.poll(),)
        if discard_old:
            event.clear()
        return next(_event_stream(events), None)
    else:
        events = event.get()
        return _event_stream(events)


def text_event(event_):
    """Takes an event and parses it so that if it is of type KEYDOWN, then it returns its character and keycode. If it
    is not of type KEYDOWN, then it returns None, None."""
    if event_ is None:
        return None, None
    elif event_.type == KEYDOWN:
        key_code = event_.key
        char = event_.unicode
        if char == '\r':
            char = '\n'
        return char, key_code
    else:
        return None, None
