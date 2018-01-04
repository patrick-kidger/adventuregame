import collections
import os
import Tools as tools


import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


_sentinel = object()


class HasAppearances:
    """Allows for setting a ((str | dict) type | tools.Container subclass) 'appearance_filenames' attribute on the
    class. If 'appearance_filename' is of type str then it is treated as being the value in a dict type input, with key
    None. The class will then have a (dict type | tools.Container subclass) 'appearances' attribute automagically added,
    whose keys are the same as that of 'appearance_filename', and whose values will be pygame.Surfaces containing the
    image(s) specified.

    'appearance_files_location' should be passed as a keyword argument to the class constructor, specifying the folder
    to look for appearance files in. Once this has been set on a parent class, all child classes will automatically use
    the same value (unless they set it to something else, of course).

    If len(appearances) == 1, for example because 'appearance_filename' was str type, then the property 'appearance'
    will automatically point at the single value in 'appearances'.

    If len(appearances) != 1, then subclasses may have an 'appearance_lookup' argument passed to them during
    initialization, specifying one of the dictionary keys. Then the property 'appearance' will point at the appropriate
    image.

    Finally, if an attribute 'size_image' is set on the class, then the class will have a pygame.Rect type 'size'
    attribute added, giving the Rect of the the image with key given by 'size_image'."""

    # Used when storing multiple appearances
    appearance_filenames = {}
    appearances = {}

    def __init_subclass__(cls, appearance_files_location=_sentinel, **kwargs):
        super(HasAppearances, cls).__init_subclass__(**kwargs)

        # So subclasses don't need to pass this as an argument, they can use whatever their parent class passed.
        if appearance_files_location is _sentinel:
            if hasattr(cls, '_appearance_files_location'):
                appearance_files_location = cls._appearance_files_location
            else:
                return
        else:
            cls._appearance_files_location = appearance_files_location

        # In particular we are not checking any of its parent classes.
        if 'appearance_filenames' in cls.__dict__:
            # This obviously feels a bit weird. A bit contrived and contrary to duck-typing. In practice we're just
            # unifying a few different similar systems under one roof.
            if isinstance(cls.appearance_filenames, str):
                appearance_filenames = {None: cls.appearance_filenames}
                cls.appearances = type(appearance_filenames)()
            elif isinstance(cls.appearance_filenames, dict):
                appearance_filenames = cls.appearance_filenames
                cls.appearances = type(appearance_filenames)()
            elif issubclass(cls.appearance_filenames, tools.Container):
                appearance_filenames = cls.appearance_filenames
                class appearances(tools.Container):
                    pass
                cls.appearances = appearances
            else:
                raise exceptions.ProgrammingException

            for name, appearance_filename in appearance_filenames.items():
                cls.appearances[name] = cls._image_from_filename(appearance_files_location, appearance_filename)

            if hasattr(cls, 'size_image'):
                cls.size = cls.appearances[cls.size_image].get_rect()

    def __init__(self, appearance_lookup=_sentinel, **kwargs):
        super(HasAppearances, self).__init__(**kwargs)
        if len(self.appearances) == 1:
            self.appearance_lookup = list(self.appearances.keys())[0]
        else:
            self.appearance_lookup = appearance_lookup

    @property
    def appearance(self):
        """The object's appearance."""
        if self.appearance_lookup is _sentinel:
            raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
        return self.appearances[self.appearance_lookup]

    @staticmethod
    def _image_from_filename(file_location, filename):
        """Takes a file location and name and returns a Surface with the specified image on it."""

        appearance_file_path = os.path.join(internal.Helpers.IMAGE_LOC, *file_location.split('/'), *filename.split('/'))
        return sdl.image.load(appearance_file_path)


# It's about twice as quick to use namedtuples over tools.Object, so it feels like we should probably use these where
# possible!
XYZPos = collections.namedtuple('XYZPos', ('x', 'y', 'z'))
XYPos = collections.namedtuple('XYPos', ('x', 'y'))
