"""Basically just a pygame wrapper, to make it easier to change it out later if need be."""

import math
import pygame
import pygame.ftfont


import Game.config.config as config

import Game.program.misc.exceptions as exceptions

# Initialise the pygame modules
pygame.ftfont.init()
pygame.display.init()
pygame.event.set_allowed(None)
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION])
pygame.key.set_repeat(config.KEY_REPEAT_DELAY, config.KEY_REPEAT)


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
error = pygame.error

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
K_a = pygame.K_a
K_b = pygame.K_b
K_c = pygame.K_c
K_d = pygame.K_d
K_e = pygame.K_e
K_f = pygame.K_f
K_g = pygame.K_g
K_h = pygame.K_h
K_i = pygame.K_i
K_j = pygame.K_j
K_k = pygame.K_k
K_l = pygame.K_l
K_m = pygame.K_m
K_n = pygame.K_n
K_o = pygame.K_o
K_p = pygame.K_p
K_q = pygame.K_q
K_r = pygame.K_r
K_s = pygame.K_s
K_t = pygame.K_t
K_u = pygame.K_u
K_v = pygame.K_v
K_w = pygame.K_w
K_x = pygame.K_x
K_y = pygame.K_y
K_z = pygame.K_z


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
    poll = pygame.event.poll
    Event = pygame.event.Event

    @classmethod
    def get(cls, num=math.inf, discard_old=False):
        """
        A generator providing a stream of events as inputs. If no events are waiting then it will return a NOEVENT.

        :int num: is the number of events to return.
        :bool discard_old: is whether to discard those events which aren't returned.
        """
        if discard_old:
            if num == math.inf:
                events = pygame.event.get()
            else:
                events = pygame.event.get()[:num]
        else:
            events = []
            for i in range(num):
                event_ = cls.poll()
                if event_.type == NOEVENT:
                    break
                events.append(event_)

        if not events:
            events = [cls.Event(NOEVENT)]

        for event_ in events:
            if event_.type == QUIT:
                raise exceptions.CloseException()
            elif event_.type == KEYDOWN:
                if event_.key in K_SHIFT:
                    continue  # The modified key will be picked up on the next keystroke
                if event_.unicode == '\r':
                    event_.unicode = '\n'
            yield event_

    @staticmethod
    def is_key(event_):
        """Checks whether an event is a KEYDOWN event."""
        return event_.type == KEYDOWN

    @staticmethod
    def is_mouse(event_, valid_buttons=(1, 2, 3)):
        """Checks whether an event is a mouse event.

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


class ftfont:
    SysFont = pygame.ftfont.SysFont


class image:
    load = pygame.image.load


class time:
    Clock = pygame.time.Clock


class key:
    get_pressed = pygame.key.get_pressed
    name = pygame.key.name

    # I can't believe there is no better way to do this.
    _names_to_code = {
        'a': K_a, 'b': K_b, 'c': K_c, 'd': K_d, 'e': K_e, 'f': K_f, 'g': K_g, 'h': K_h, 'i': K_i, 'j': K_j, 'k': K_k,
        'l': K_l, 'm': K_m, 'n': K_n, 'o': K_o, 'p': K_p, 'q': K_q, 'r': K_r, 's': K_s, 't': K_w, 'u': K_u, 'v': K_v,
        'w': K_w, 'x': K_x, 'y': K_y, 'z': K_z,
    }

    @classmethod
    def code(cls, key_name):
        return cls._names_to_code[key_name]


# Custom stuff
K_SHIFT = (K_LSHIFT, K_RSHIFT)
K_ENTER = (K_KP_ENTER, K_RETURN)
MOUSEEVENTS = (MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION)
