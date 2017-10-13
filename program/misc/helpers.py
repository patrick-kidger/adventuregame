import re
import os

import Tools as tools

import Maze.program.misc.sdl as sdl


def appearance_metaclass(files_location):
    class AppearanceMetaclass(type):
        """Allows for setting an appearance_filename attribute on the class, which will then have an 'appearance'
        attribute automagically added, which will be a Surface containing the image specified."""
        def __init__(cls, name, bases, dct):
            if not hasattr(cls, '_appearance_filename') or cls.appearance_filename != cls._appearance_filename:
                appearance_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', files_location,
                                                    cls.appearance_filename)
                cls.appearance = sdl.image.load(appearance_file_path)
                # Keep a record of what the current appearance has been set to. So if a subclass doesn't set a new
                # appearance_filename, we don't need to load up another copy of the image, we can just the one on the
                # parent class.
                cls._appearance_filename = cls.appearance_filename
            super(AppearanceMetaclass, cls).__init__(name, bases, dct)
    return AppearanceMetaclass


class HasPositionMixin(object):
    """Gives the class a notion of x, y, z position."""

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


def input_(num_chars=1, output=None, flush=None):
    """A pygame equivalent to the builtin input() function. (Without being able to pass a prompt string.)

    :int num_chars: the number of characters of input that it should accept before automatically preventing further
        input. May be set to math.inf to go forever.
    :callable output: If specified, then each character of the user-typed input will be passed as an argument to this
        callable, presumably so that it can be outputted to the screen.
    :callable flush: If specified, then this function will be called after each character of the user-typed input has
        been received, presumably so that if need be, the screen it has been printed to can be flushed."""

    def _get_char():
        """Gets a single character."""
        while True:
            sdl.event.clear()
            event = sdl.event.wait()
            if event.type == sdl.QUIT:
                raise KeyboardInterrupt
            elif event.type == sdl.KEYDOWN:
                char = event.unicode
                if char == '\r':
                    char = '\n'
                key_code = event.key
                if key_code in sdl.K_SHIFT:
                    continue  # The modified key will be picked up on the next keystroke.
                break
        if output is not None:
            output(char)
        if flush is not None:
            flush()
        return char, key_code

    returnstr = ''
    i = 0
    while i < num_chars:
        char, key_code = _get_char()
        if key_code in sdl.K_ENTER:
            break
        elif key_code == sdl.K_BACKSPACE:
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
