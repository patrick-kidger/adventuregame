import collections
import os
import Tools as tools


import Game.config.internal_strings as internal_strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


def appearance_from_filename(files_location):
    """Allows for setting an 'appearance_filename' attribute on the class, which will then have an 'appearance'
    attribute automagically added, which will be a Surfaces containing the images specified.

    If an 'appearance_filenames' attribute is set, expected to be a dictionary, then an 'appearances' attribute will
    be added. In this case the subclass should have an 'appearance_lookup' argument passed to it on initialisation,
    specifying the dictionary key to use to find the appropriate appearance."""

    class Appearance:
        appearance_filenames = collections.OrderedDict()
        _appearance_filenames_id = id(appearance_filenames)
        appearance_filename = None
        _appearance_filename_id = id(appearance_filename)

        __sentinel = object()
        def __init__(self, appearance_lookup=__sentinel, **kwargs):
            if self.has_multiple_appearances:
                if appearance_lookup is self.__sentinel:
                    raise exceptions.ProgrammingException(internal_strings.Exceptions.NO_APPEARANCE_LOOKUP)
                else:
                    self.appearance_lookup = appearance_lookup

        def __init_subclass__(cls, **kwargs):
            super(Appearance, cls).__init_subclass__(**kwargs)
            cls.update_appearance()

        @property
        def has_multiple_appearances(self):
            return hasattr(self, 'appearances')

        @classmethod
        def _appearance_from_filename(cls, filename):
            appearance_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                                                *files_location.split('/'),
                                                *filename.split('/'))
            return sdl.image.load(appearance_file_path)

        @classmethod
        def update_appearance(cls):
            """Should be called after setting appearance_filename or appearance_filenames, to update the appearance."""

            if id(cls.appearance_filename) != cls._appearance_filename_id:
                cls.appearance = cls._appearance_from_filename(cls.appearance_filename)
                # Keep a record of what the current appearance has been set to. So if e.g. a subclass doesn't set
                # a new appearance_filename, we don't need to load up another copy of the image, we can just use
                # the appearance attribute on the parent class.
                cls._appearance_filename_id = id(cls.appearance_filename)

            if id(cls.appearance_filenames) != cls._appearance_filenames_id:
                cls.appearances = collections.OrderedDict()
                for name, appearance_filename in cls.appearance_filenames.items():
                    cls.appearances[name] = cls._appearance_from_filename(appearance_filename)
                    cls._appearance_filenames_id = id(cls.appearance_filenames)
                cls.appearance = property(lambda self: self.appearances[self.appearance_lookup])

    return Appearance


def image_from_filename(files_location):
    """Allows for setting a class 'ImageFilenames' as an attribute, listing all of the images that should be loaded.
    A class called 'Images' will be then be added, providing references to Surfaces containing the specified images.

    The class 'ImageFilenames' should inherit from Container, which is given in mixins.py. (Probably referenced as
    Tools.Container)."""

    class ImageGetter:
        class ImageFilenames(tools.Container):
            pass

        def __init_subclass__(cls, **kwargs):
            super(ImageGetter, cls).__init_subclass__(**kwargs)
            class Images(tools.Container):
                pass
            cls.Images = Images
            cls.update_images()

        @tools.classproperty
        def size(cls):
            return getattr(cls.Images, cls.size_image).get_rect()

        @tools.combomethod
        def update_images(self_or_cls, image_identifier=None):
            """Should be called after setting ImageFilenames, to update them. It may be called as either a class or an
            instance method, which will set the Image attribute on the class or instance respectively."""
            if image_identifier is None:
                files_to_handle = self_or_cls.ImageFilenames
            else:
                files_to_handle = ((image_identifier, getattr(self_or_cls.ImageFilenames, image_identifier)),)

            for image_identifier_, image_filename in files_to_handle.items():
                image_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                                               *files_location.split('/'),
                                               *image_filename.split('/'))
                setattr(self_or_cls.Images, image_identifier_, sdl.image.load(image_file_path))

    return ImageGetter


class AlignmentMixin:
    """Provides methods for placing objects on the instances's screen."""

    def _align(self, image_rect, horz_alignment=internal_strings.Alignment.CENTER, vert_alignment=internal_strings.Alignment.CENTER):
        """Takes a rectangle and some alignment options and returns the coordinates that the top left of the rectangle
        should be at on the instance's screen.

        :Rect image_rect: pygame.Rect instance of the object to tbe placed.
        :str horz_alignment: Optional string describing where the object should be placed.
        :str vert_alignment: Optional string describing where the object should be placed.
        """
        screen_rect = self.screen.get_rect()
        if horz_alignment == internal_strings.Alignment.LEFT:
            horz_pos = 0
        elif horz_alignment == internal_strings.Alignment.RIGHT:
            horz_pos = screen_rect.width - image_rect.width
        elif horz_alignment == internal_strings.Alignment.CENTER:
            horz_pos = (screen_rect.width - image_rect.width) // 2
        else:
            horz_pos = horz_alignment

        if vert_alignment == internal_strings.Alignment.TOP:
            vert_pos = 0
        elif vert_alignment == internal_strings.Alignment.BOTTOM:
            vert_pos = screen_rect.height - image_rect.height
        elif vert_alignment == internal_strings.Alignment.CENTER:
            vert_pos = (screen_rect.height - image_rect.height) // 2
        else:
            vert_pos = vert_alignment

        return horz_pos, vert_pos

    def _view(self, image_rect, horz_alignment=internal_strings.Alignment.CENTER, vert_alignment=internal_strings.Alignment.CENTER):
        """As _align, but returns a subsurface of the instance's screen corresponding to where :image_rect: should be
        placed."""
        horz_pos, vert_pos = self._align(image_rect, horz_alignment, vert_alignment)
        image_rect = sdl.Rect(horz_pos, vert_pos, image_rect.width, image_rect.height)
        return self.screen.subsurface(image_rect)


class EnablerMixin:
    """Gives instances an 'enabled' attribute, along with some methods to set its value."""
    def __init__(self, enabled, *args, **kwargs):
        self.enabled = enabled
        super(EnablerMixin, self).__init__(*args, **kwargs)

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
