import os
import Tools as tools


import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


_sentinel = object()


class _ImageGetter:
    """Just provides one helper function, wrapped in a class for convenience."""

    @classmethod
    def _image_from_filename(cls, file_location, filename):
        """Takes a file location and name and returns a Surface with the specified image on it."""

        appearance_file_path = os.path.join(internal.Helpers.IMAGE_LOC, *file_location.split('/'), *filename.split('/'))
        return sdl.image.load(appearance_file_path)


class HasImages(_ImageGetter):
    """Allows for setting a class type attribute 'ImageFilenames', specifying a list of images that should be loaded.
    A class type attribute 'Images' will be then be added, providing references to Surfaces containing the specified
    images.

    The class 'ImageFilenames' should inherit from Container, which is given in Tools/mixins.py. (Probably referenced as
    tools.Container).

    If the class also specifies a string type 'size_image' attribute then a Rect type 'size' attribute will be added
    giving the Rect of the image whose identifier is given by 'size_image'.

    Example usage:
    >>> class Button(HasImages, images_location='image/files/location'):
    ... size_image = 'button_base'
    ... class ImageFilenames(tools.Container):
    ...     button_base = 'general/button/button1.png'
    ...     button_deselect = 'general/button/button2.png'
    ...     button_select = 'general/button/button3.png'
    """

    class ImageFilenames(tools.Container):
        pass

    def __init_subclass__(cls, images_location=_sentinel, **kwargs):
        super(HasImages, cls).__init_subclass__(**kwargs)

        # So subclasses don't need to pass this as an argument, they can use whatever their parent class passed.
        if images_location is _sentinel:
            if hasattr(cls, '_images_location'):
                images_location = cls._images_location
            else:
                raise exceptions.ProgrammingException(strings.Exceptions.NO_FILE_LOCATION)
        else:
            cls._images_location = images_location

        class Images(tools.Container):
            pass

        for image_identifier, image_filename in cls.ImageFilenames.items():
            image = cls._image_from_filename(images_location, image_filename)
            setattr(Images, image_identifier, image)
        cls.Images = Images

        if hasattr(cls, 'size_image'):
            cls.size = getattr(cls.Images, cls.size_image).get_rect()


# For a while this also handled having a single appearance as a special case (setting just
# appearance_filename = 'some_string'), but having the two systems side-by-side proved to be more complicated than it
# was worth, and I didn't really want to create a whole new class ('HasAppearance', singular) to handle a special case
# of this one, not least because the inheritance trees of their subclasses then get that much more complicated, with
# some of them inheriting from one, some of them inheriting from the other.
class HasAppearances(_ImageGetter):
    """Allows for setting a dict type 'appearance_filenames' attribute on the class, which will then have a dict type
     'appearances' attribute automagically added, whose values will be pygame.Surfaces containing the image specified.

    If the dictionary contains more than one entry, then subclasses should have an 'appearance_lookup' argument passed
    during initialisation, specifying the dictionary key to use to find the appropriate appearance. (This will be
    handled automatically if there is only once choice of appearance.) This value be altered after initialisation, if
    desired, by assigning to the 'appearance_lookup' attribute."""

    # Used when storing multiple appearances
    appearance_filenames = {}
    _appearance_filenames_id = id(appearance_filenames)
    appearances = None
    # Immediately redefined in subclasses
    appearance = None
    # Subclasses should define this to set where it should look for the appearance files.
    files_location = None

    def __init_subclass__(cls, appearance_files_location=_sentinel, **kwargs):
        super(HasAppearances, cls).__init_subclass__(**kwargs)

        # So subclasses don't need to pass this as an argument, they can use whatever their parent class passed.
        if appearance_files_location is _sentinel:
            if hasattr(cls, '_appearance_files_location'):
                appearance_files_location = cls._appearance_files_location
            else:
                raise exceptions.ProgrammingException(strings.Exceptions.NO_FILE_LOCATION)
        else:
            cls._appearance_files_location = appearance_files_location

        if id(cls.appearance_filenames) != cls._appearance_filenames_id:
            # Keep a record of what the current appearance has been set to. So if e.g. a subclass doesn't set
            # a new appearance_filename, we don't need to load up another copy of the image, we can just use
            # the appearance attribute on the parent class.
            cls._appearance_filenames_id = id(cls.appearance_filenames)

            cls.appearances = type(cls.appearance_filenames)()
            for name, appearance_filename in cls.appearance_filenames.items():
                cls.appearances[name] = cls._image_from_filename(appearance_files_location, appearance_filename)

    def __init__(self, appearance_lookup=_sentinel, **kwargs):
        super(HasAppearances, self).__init__(**kwargs)
        # So that we don't get HasAppearances or any of its subclasses defined before we start putting appearances on.
        if self.appearances is not None:
            if appearance_lookup is _sentinel:
                if len(self.appearances) == 1:
                    self.appearance_lookup = list(self.appearances.keys())[0]
                else:
                    raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
            else:
                self.appearance_lookup = appearance_lookup

    @property
    def appearance(self):
        """The object's appearance."""
        return self.appearances[self.appearance_lookup]


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
