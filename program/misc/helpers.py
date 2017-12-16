import os
import Tools as tools


import Game.config.internal_strings as internal_strings

import Game.program.misc.sdl as sdl


def appearance_from_filename(files_location):
    """Allows for setting an 'appearance_filename' attribute on the class, which will then have an 'appearance'
    attribute automagically added, which will be a Surface containing the image specified."""

    class Appearance:
        _appearance_filename = None
        appearance_filename = None

        def __init_subclass__(cls, **kwargs):
            super(Appearance, cls).__init_subclass__(**kwargs)
            cls.update_appearance()

        @tools.combomethod
        def update_appearance(self_or_cls):
            """Should be called after setting appearance_filename, to update the appearance. It may be called as either
            a class or an instance method, which will set the appearance attribute on the class or instance
            respectively."""

            if self_or_cls.appearance_filename != self_or_cls._appearance_filename:
                appearance_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'images',
                                                    *files_location.split('/'),
                                                    *self_or_cls.appearance_filename.split('/'))
                self_or_cls.appearance = sdl.image.load(appearance_file_path)
                # Keep a record of what the current appearance has been set to. So if e.g. a subclass doesn't set a new
                # appearance_filename, we don't need to load up another copy of the image, we can just use the
                # appearance attribute on the parent class.
                self_or_cls._appearance_filename = self_or_cls.appearance_filename

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


class HasPositionMixin:
    """Gives the class a notion of x, y, z position."""

    def __init__(self, pos=None):
        self.pos = tools.Object(x=0, y=0, z=0)
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

    @x.setter
    def x(self, val):
        self.pos.x = val

    @y.setter
    def y(self, val):
        self.pos.y = val

    @z.setter
    def z(self, val):
        self.pos.z = val


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
