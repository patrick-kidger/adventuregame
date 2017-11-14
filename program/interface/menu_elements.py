import collections
import Tools as tools


import config.config as config

import program.interface.base as base
import program.misc.helpers as helpers
import program.misc.sdl as sdl


def _pos_diff(pos_a, pos_b):
    """The difference of two positions."""
    return pos_a[0] - pos_b[0], pos_a[1] - pos_b[1]


def _pos_add(pos_a, pos_b):
    """The sum of two positions."""
    return pos_a[0] + pos_b[0], pos_a[1] + pos_b[1]


class MenuElement(helpers.image_from_filename(config.INTERFACE_FOLDER)):
    """Base class for all menu elements.

    Subclasses should define click(self, pos) and unclick(self) methods which determine what happens when a click is
    made at the given position, and when the element is deselected by the user clicking elsewhere.

    When initialising menu elements, they should be passed a pygame.Surface object to use to store what the element
    currently looks like, graphically. It is expected that this will in fact be a subsurface of an overlay's screen, so
    that changes to the menu element's screen automatically get forwarded to the overlay's screen. (And is why the
    screen is passed as an initialisation argument rather than being created within __init__.)

    Menu elements may also define a class attribute 'ImageFilenames', which will be iterated over to find the locations
    of the image files determining what the menu element looks like. The loaded images will then be stored in an
    attribute called 'Images', with the same names as they were defined with in ImageFilenames.

    Menu elements may define a class attribute 'size_image', which is the name of one of the loaded images, that will
    be used to determine how large the menu element is, for example when determining its alignment on the screen. Note
    that the value 'size_image' should be a string referring to the name of the python variable usedin 'ImageFilenames',
    not the name of the file that it refers to.

    Note that the position in the 'click' method is expected to be given in terms of the position of the click on the
    overall display, so self._screen_pos should be called on the position to determine the position relative to the
    screen that this element uses."""

    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        super(MenuElement, self).__init__(*args, **kwargs)

    def screen_pos(self, pos):
        """Converts a position on the parent screen into a position relative to the screen used for this menu element.
        """
        subsurface_offset = self.screen.get_offset()  # If the screen is a subsurface then we need to take into account
                                                      # the offset between it and its parent surface.
        viewport_offset = self.screen.get_viewport_offset()  # If the screen is using a viewport then we also need to
                                                             #  add on the offset from that.
        total_offset = _pos_add(subsurface_offset, viewport_offset)
        return _pos_diff(pos, total_offset)

    def point_within(self, pos):
        """Whether or not the given point is within the boundaries of this menu component."""
        return self.screen.point_within(pos)

    def click(self, pos):
        pass

    def unclick(self):
        pass


class MultipleComponentMixin(object):
    def click(self, pos):
        for count, component in enumerate(self.components.values()):
            if component.point_within(pos):
                component_pos = component.screen_pos(pos)
                click_result = component.click(component_pos)
                return tools.Object(count=count, component=component, click_result=click_result)
        else:
            return tools.Object(count=None, component=None, click_result=None)


class Button(MenuElement, base.FontMixin, helpers.AlignmentMixin):
    """A button with text on it."""

    size_image = 'button_base'

    class ImageFilenames(tools.Container):
        button_base = 'general/button/button_base.png'
        button_deselect = 'general/button/button_deselect.png'
        button_select = 'general/button/button_select.png'

    def __init__(self, text, *args, **kwargs):
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])
        super(Button, self).__init__(*args, **kwargs)
        self.screen.blit(self.Images.button_base)
        self.screen.blit(self.Images.button_deselect)
        button_text = self.render_text(text)
        text_centered = self._align(button_text.get_rect(), **align_kwargs)
        self.screen.blit(button_text, text_centered)

    def click(self, pos):
        self.screen.blit(self.Images.button_select)

    def unclick(self):
        self.screen.blit(self.Images.button_deselect)


class Entry(Button):
    """An entry in a List. Each entry has text on it."""

    class ImageFilenames(tools.Container):
        button_base = 'general/list/list_entry_base.png'
        button_deselect = 'general/list/list_entry_deselected.png'
        button_select = 'general/list/list_entry_selected.png'


class Entries(MenuElement, MultipleComponentMixin, base.FontMixin):

    horz_text_offset = 18

    class ImageFilenames(tools.Container):
        entries_background = 'general/list/entries_background.png'

    def __init__(self, entry_text, entry_size, *args, **kwargs):
        super(Entries, self).__init__(*args, **kwargs)
        self.screen.blit(self.Images.entries_background)

        self.components = collections.OrderedDict()
        self.clicked_entry = None

        for count, text in enumerate(entry_text):
            entry_rect = sdl.Rect(0, entry_size.height * count, entry_size.width, entry_size.height)
            entry_screen = self.screen.subsurface(entry_rect)
            entry = Entry(screen=entry_screen, text=text, font=self.font, horz_alignment=self.horz_text_offset)
            self.components[count] = entry


class Scrollbar(MenuElement):

    class ImageFilenames(tools.Container):
        scrollbar_background = 'general/list/scrollbar_background.png'
        scroll_handle = 'general/list/list_scroll_handle.png'

    def __init__(self, *args, **kwargs):
        super(Scrollbar, self).__init__(*args, **kwargs)
        self.screen.blit(self.Images.scrollbar_background)
        self.screen.blit(self.Images.scroll_handle)


class List(MenuElement, MultipleComponentMixin, base.FontMixin):
    """A scrollable list of entries."""

    size_image = 'list_background'

    class ImageFilenames(tools.Container):
        list_background = 'general/list/list_background.png'

    class Alignment(object):  # Tidied up into a class here rather than keeping them all as individual variables.
        entry_size = sdl.Rect((0, 0), (747, 150))  # How big each entry in the list is

        entry_cutout = sdl.Rect((5, 60), (747, 735))  # Cutout in the main screen for entries
        entry_view = sdl.Rect((0, 0), (747, 735))     # View of the entries screen

        scrollbar_cutout = sdl.Rect((757, 60), (38, 735))  # Cutout in the main screen for the scrollbar

        title_offset = (8, 8)

    def __init__(self, title, entry_text, font, *args, **kwargs):
        super(List, self).__init__(font=font, *args, **kwargs)
        self.screen.blit(self.Images.list_background)
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)
        self.screen.blit(Entries.Images.entries_background, self.Alignment.entry_cutout.topleft)

        self.scroll_screen_view = None
        self.clicked_entry = None
        self.components = tools.Object()

        entry_view = sdl.Surface((self.Alignment.entry_size.width, self.Alignment.entry_size.height * len(entry_text)),
                                 viewport=self.Alignment.entry_view)
        scrollbar_screen = self.screen.subsurface(self.Alignment.scrollbar_cutout)
        self.screen.cutout(location=self.Alignment.entry_cutout, target=entry_view)

        self.components.entries = Entries(screen=entry_view, font=font, entry_text=entry_text,
                                          entry_size=self.Alignment.entry_size)
        self.components.scrollbar = Scrollbar(screen=scrollbar_screen)

        self._update_scroll_view()

    def _update_scroll_view(self):
        """Updates how the entries are scrolled, e.g. in response to using the scroll bar."""
        self.screen.update()

    def click(self, pos):
        click_result = super(List, self).click(pos)
        if click_result.component is self.components.entries:
            self._update_scroll_view()
            self.clicked_entry = click_result.click_result.component
            return click_result.click_result.count
        else:
            self.clicked_entry = None
            return None

    def unclick(self):
        if self.clicked_entry is not None:
            self.clicked_entry.unclick()
            self._update_scroll_view()
