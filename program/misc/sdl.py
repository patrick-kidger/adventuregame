"""Basically just a pygame wrapper, to make it easier to change it out later if need be."""

import pygame
import pygame.ftfont
import pygame.display
import pygame.event


import Game.config.config as config

import Game.program.misc.exceptions as exceptions

# Initialise the pygame modules
pygame.ftfont.init()
pygame.display.init()
pygame.event.set_allowed(None)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])
pygame.key.set_repeat(config.KEY_REPEAT, config.KEY_REPEAT)


# Top-level pygame imports
class Surface(pygame.Surface):
    def __init__(self, *args, viewport=None, **kwargs):
        super(Surface, self).__init__(*args, **kwargs)
        # Allows for setting the offset for non-subsurfaces.
        self._init(viewport=viewport)

    def _init(self, viewport):
        if viewport is None:
            viewport = self.get_rect()
        self.viewport = viewport
        self._cutouts = []
        self._offset = None

    def cutout(self, location, target):
        target._set_offset(location.topleft)
        self._cutouts.append(target)

    def update_cutouts(self):
        for cutout in self._cutouts:
            cutout.update_cutouts()
            view = cutout.get_view_from_viewport()
            location = cutout.get_offset()
            self.blit(view, location)

    def _set_offset(self, offset):
        self._offset = offset

    # Can't just call it 'get_view' as that is something else entirely, built-in to pygame.Surface already.
    def get_view_from_viewport(self):
        clipped_viewport = self.get_rect().clip(self.viewport)
        return self.subsurface(clipped_viewport)

    def subsurface(self, *args, viewport=None, **kwargs):
        return_surface = super(Surface, self).subsurface(*args, **kwargs)
        return_surface._init(viewport=viewport)
        return return_surface

    def get_offset(self):
        if self._offset is not None:
            return self._offset
        else:
            return super(Surface, self).get_offset()

    def get_abs_offset(self):
        if self._offset is not None:
            # Should only occur for non-subsurfaces, as __init__ is only called when creating a new Surface.
            return self._offset
        else:
            return super(Surface, self).get_abs_offset()

    def get_viewport_offset(self):
        return self.viewport.topleft

    def blit(self, source, dest=(0, 0), *args, **kwargs):  # Added default argument to dest
        return super(Surface, self).blit(source, dest, *args, **kwargs)

    def point_within(self, pos):
        offset = self.get_offset()
        rect = self.get_rect(left=offset[0], top=offset[1])
        return rect.collidepoint(pos)


Rect = pygame.Rect
quit = pygame.quit

# Event types
NOEVENT = pygame.NOEVENT
QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
MOUSEMOTION = pygame.MOUSEMOTION
# And top-level keycodes
K_LSHIFT = pygame.K_LSHIFT
K_RSHIFT = pygame.K_RSHIFT
K_BACKSPACE = pygame.K_BACKSPACE
K_RETURN = pygame.K_RETURN
K_KP_ENTER = pygame.K_KP_ENTER
K_ESCAPE = pygame.K_ESCAPE
K_BACKSLASH = pygame.K_BACKSLASH
K_SLASH = pygame.K_SLASH
K_UP = pygame.K_UP
K_DOWN = pygame.K_DOWN


# Emulate its modules
class display:
    # Note that set_mode will return a pygame.Surface, not the enhanced Surface defined above. It's not possible to
    # reassign its __class__ as Surface is a builtin type.
    set_mode = pygame.display.set_mode
    set_caption = pygame.display.set_caption
    update = pygame.display.update


class event:
    clear = pygame.event.clear
    wait = pygame.event.wait
    get = pygame.event.get
    poll = pygame.event.poll
    Event = pygame.event.Event


class ftfont:
    SysFont = pygame.ftfont.SysFont


class image:
    load = pygame.image.load


class time:
    Clock = pygame.time.Clock


# Custom stuff
K_SHIFT = (K_LSHIFT, K_RSHIFT)
K_ENTER = (K_KP_ENTER, K_RETURN)
MOUSEEVENTS = (MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION)


def event_stream(single_event=False, discard_old=True):
    """A generator providing a stream of events as inputs.

    If single_event is True, then it will instead just return a single event, or a blank event if there is no event in
    the queue.
    If discard_old is also True, then it will discard all the other events.
    """
    def _event_stream(events):
        for event_ in events:
            if event_.type == QUIT:
                raise exceptions.CloseException()
            elif event_.type == KEYDOWN:
                if event_.key in K_SHIFT:
                    continue  # The modified key will be picked up on the next keystroke
                if event_.unicode == '\r':
                    event_.unicode = '\n'
            yield event_

    if single_event:
        events = (event.poll(),)
        if discard_old:
            event.clear()
        return next(_event_stream(events), event.Event(NOEVENT))
    else:
        events = event.get()
        return _event_stream(events)


def key_event(event_):
    """Checks whether an event is a KEYDOWN event."""
    return event_.type == KEYDOWN


def mouse_event(event_, valid_buttons=(1, 2, 3)):
    """Takes an event and parses it so that if it is a mouse-related event relating to the specified mouse button, then
    it returns it. Else it returns a blank event. As such all calls to this should probably be followed by checking the
    type of its return value.

    Meaning of :valid_buttons: elements:
    1 - Left click
    2 - Middle click
    3 - Right click
    4 - Scroll wheel up
    5 - Scroll wheel down
    6 - Mouse 4
    7 - Mouse 5"""

    if event_.type not in MOUSEEVENTS:
        return False
    if event_.type != MOUSEMOTION and event_.button not in valid_buttons:
        return False
    return True
