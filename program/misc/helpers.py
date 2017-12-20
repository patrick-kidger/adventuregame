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
                raise exceptions.ProgrammingException(strings.Exceptions.BAD_APPEARANCE_FILENAME)

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


class AlignmentMixin:
    """Provides methods for placing objects on the instances's screen. The instance must already have a screen for this
    to work - this mixin does not provide one."""

    def _align(self, image_rect, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """Takes a rectangle and some alignment options and returns the coordinates that the top left of the rectangle
        should be at on the instance's screen.

        :Rect image_rect: pygame.Rect instance of the object to tbe placed.
        :str horz_alignment: Optional string describing where the object should be placed.
        :str vert_alignment: Optional string describing where the object should be placed.
        """

        screen_rect = self.screen.get_rect()
        if horz_alignment == internal.Alignment.LEFT:
            horz_pos = 0
        elif horz_alignment == internal.Alignment.RIGHT:
            horz_pos = screen_rect.width - image_rect.width
        elif horz_alignment == internal.Alignment.CENTER:
            horz_pos = (screen_rect.width - image_rect.width) // 2
        else:
            horz_pos = horz_alignment

        if vert_alignment == internal.Alignment.TOP:
            vert_pos = 0
        elif vert_alignment == internal.Alignment.BOTTOM:
            vert_pos = screen_rect.height - image_rect.height
        elif vert_alignment == internal.Alignment.CENTER:
            vert_pos = (screen_rect.height - image_rect.height) // 2
        else:
            vert_pos = vert_alignment

        return horz_pos, vert_pos

    def _view(self, image_rect, horz_alignment=internal.Alignment.CENTER, vert_alignment=internal.Alignment.CENTER):
        """As _align, but returns a subsurface of the instance's screen corresponding to where :image_rect: should be
        placed."""

        horz_pos, vert_pos = self._align(image_rect, horz_alignment, vert_alignment)
        image_rect = sdl.Rect(horz_pos, vert_pos, image_rect.width, image_rect.height)
        return self.screen.subsurface(image_rect)


class EnablerMixin:
    """Gives instances an 'enabled' attribute, along with some methods to set its value."""

    def __init__(self, enabled, **kwargs):
        self.enabled = enabled
        super(EnablerMixin, self).__init__(**kwargs)

    def toggle(self):
        """Toggles the 'enabled' attribute."""
        self.enabled = not self.enabled

    def enable(self, state=True):
        """Sets the 'enabled' attribute to :state:, or True if no :state: argument is passed."""
        self.enabled = state

    def disable(self):
        """Sets the 'enabled' attribute to False."""
        self.enable(False)

    def use(self):
        """Temporarily sets the enabled attribute to True. Used with a with statement."""
        return tools.set_context_variable(self, 'enabled')
