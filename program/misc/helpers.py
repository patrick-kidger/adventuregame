import re
import os
import Tools as tools

import program.misc.sdl as sdl


def appearance_from_filename(files_location):
    """Allows for setting an appearance_filename attribute on the class, which will then have an 'appearance' attribute
    automagically added, which will be a Surface containing the image specified."""

    class AppearanceMetaclass(type):
        def __init__(cls, name, bases, dct):
            cls.update_appearance()
            super(AppearanceMetaclass, cls).__init__(name, bases, dct)

    class Appearance(object, metaclass=AppearanceMetaclass):
        _appearance_filename = None
        appearance_filename = None

        @tools.combomethod
        def update_appearance(self_or_cls):
            """Should be called after setting appearance_filename, to update the appearance. It may be called as either
            a class or an instance method, which will set the appearance attribute on the class or instance
            respectively."""
            if self_or_cls.appearance_filename != self_or_cls._appearance_filename:
                appearance_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'images', files_location,
                                                    self_or_cls.appearance_filename)
                self_or_cls.appearance = sdl.image.load(appearance_file_path)
                # Keep a record of what the current appearance has been set to. So if e.g. a subclass doesn't set a new
                # appearance_filename, we don't need to load up another copy of the image, we can just use the
                # appearance attribute on the parent class.
                self_or_cls._appearance_filename = self_or_cls.appearance_filename

    return Appearance


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


class EnablerMixin(object):
    def __init__(self, enabled):
        self.enabled = enabled
        super(EnablerMixin, self).__init__()

    def toggle(self):
        self.enabled = not self.enabled

    def enable(self, state=True):
        self.enabled = state

    def disable(self):
        self.enabled = False

    def use(self):
        """Sets the enabled attribute temporarily. Used with a with statement."""

        class EnablerClass(tools.WithAnder):
            def __enter__(self_enabler):
                self_enabler.enabled = self.enabled
                self.enabled = True

            def __exit__(self_enabler, exc_type, exc_val, exc_tb):
                self.enabled = self_enabler.enabled

        return EnablerClass()


def re_sub_recursive(pattern, sub, inputstr):
    patt = re.compile(pattern)

    old_inputstr = inputstr
    inputstr = patt.sub(sub, inputstr)
    while old_inputstr != inputstr:
        old_inputstr = inputstr
        inputstr = patt.sub(sub, inputstr)

    return inputstr
