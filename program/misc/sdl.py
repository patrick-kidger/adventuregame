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

# Event types
QUIT = pygame.QUIT
KEYDOWN = pygame.KEYDOWN
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


def text_stream(single_event=False, discard_old=True):
    """A generator providing a stream of all of the text input."""
    def _text_stream(events):
        for event_ in events:
            if event_.type == QUIT:
                raise KeyboardInterrupt
            elif event_.type == KEYDOWN:
                key_code = event_.key
                if key_code in K_SHIFT:
                    continue  # The modified key will be picked up on the next keystroke
                char = event_.unicode
                if char == '\r':
                    char = '\n'
                yield char, key_code

    if single_event:
        events = (event.poll(),)
        if discard_old:
            event.clear()
        return next(_text_stream(events), (None, None))
    else:
        events = event.get()
        return _text_stream(events)


def modify_text(text, done=(K_KP_ENTER, K_RETURN, K_ESCAPE), char_done=tuple(), output=None, flush=None):
    """Modifies the given text based on inputted text events."""
    char = None
    key_code = None
    should_output = True
    for char, key_code in text_stream():
        if key_code in done or char in char_done:
            break
        elif key_code == K_BACKSPACE:
            # Disable outputting backspaces if we're not actually modifying the text with them.
            if len(text) == 0:
                should_output = False
            text = text[:-1]
        else:
            text += char

        if output is not None:
            # Don't output backspaces if the text we're modifying hasn't been changed because of it.
            if should_output:
                output(char)
                if flush is not None:
                    flush()
    return text, char, key_code
