import re
import pygame

import Tools as tools


class HasPositionMixin(object):
    def __init__(self, pos=None):
        self.pos = tools.Object('x', 'y', 'z', default_value=0)
        if pos is not None:
            self.set_pos(pos)
        super(HasPositionMixin, self).__init__()
        
    def set_pos(self, pos):
        """Initialises the object based on the data to load."""
        self.pos.x = pos.x
        self.pos.y = pos.y
        self.pos.z = pos.z
        
    @property
    def x(self):
        """The object's current x position."""
        return self.pos.x
        
    @property
    def y(self):
        """The object's current y position."""
        return self.pos.y
        
    @property
    def z(self):
        """The object's current z position."""
        return self.pos.z


def input_pygame(num_chars=1, output=None, **kwargs):
    """A pygame equivalent to the builtin input() function. (Without being able to pass a prompt string.)

    :int num_chars: the number of characters of input that it should accept before automatically preventing further
        input. May be set to math.inf to go forever.
    :callable output: If specified, then each character of the user-typed input will be passed as an argument to this
        callable, presumably so that it can be outputted to the screen. Any additional keyword arguments are passed as
        arguments to the output call, if it is made."""

    def _get_char():
        """Gets a single character."""
        while True:
            pygame.event.clear()
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            elif event.type == pygame.KEYDOWN:
                char = event.unicode
                if char == '\r':
                    char = '\n'
                key_code = event.key
                if key_code in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    continue  # The modified key will be picked up on the next keystroke.
                break
        if output is not None:
            output(char, **kwargs)
        return char, key_code

    returnstr = ''
    i = 0
    while i < num_chars:
        char, key_code = _get_char()
        if key_code in (pygame.K_KP_ENTER, pygame.K_RETURN):
            break
        elif key_code == pygame.K_BACKSPACE:
            if i >= 1:
                returnstr = returnstr[:-1]
                i -= 1
        else:
            returnstr += char
            i += 1
    return returnstr


def re_sub_recursive(pattern, sub, inputstr):
    patt = re.compile(pattern)
    inputstrlen = len(inputstr)
    inputstr = patt.sub(sub, inputstr)

    while len(inputstr) != inputstrlen:
        inputstrlen = len(inputstr)
        inputstr = patt.sub(sub, inputstr)

    return inputstr
