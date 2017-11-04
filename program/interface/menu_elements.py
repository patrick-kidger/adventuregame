import Tools as tools


import config.config as config

import program.interface.base as base
import program.misc.helpers as helpers
import program.misc.sdl as sdl


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

    def _screen_pos(self, pos):
        """Converts a position on the main display screen into a position relative to the screen used for this menu
        element."""
        offset = self.screen.get_abs_offset()
        return self.pos_diff(pos, offset)

    @staticmethod
    def pos_diff(pos_a, pos_b):
        """The difference of two positions."""
        return pos_a[0] - pos_b[0], pos_a[1] - pos_b[1]


class Button(MenuElement, base.FontMixin, helpers.AlignmentMixin):
    """A button with text on it."""

    size_image = 'button_base'

    class ImageFilenames(tools.Container):
        button_base = 'general/button/button_base.png'
        button_deselect = 'general/button/button_deselect.png'
        button_select = 'general/button/button_select.png'

    def __init__(self, screen, text, font, *args, **kwargs):
        super(Button, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.screen.blit(self.Images.button_base)
        self.screen.blit(self.Images.button_deselect)
        button_text = self.render_text(text)
        text_centered = self._align(button_text.get_rect())
        self.screen.blit(button_text, text_centered)

    def click(self, pos):
        self.screen.blit(self.Images.button_select)

    def unclick(self):
        self.screen.blit(self.Images.button_deselect)


class _Entry(MenuElement, base.FontMixin):
    """An entry in a List. Each entr has text on it."""

    size_image = 'list_entry_base'

    text_offset = (18, 18)

    class ImageFilenames(tools.Container):
        list_entry_base = 'general/list/list_entry_base.png'
        list_entry_deselected = 'general/list/list_entry_deselected.png'
        list_entry_selected = 'general/list/list_entry_selected.png'

    def __init__(self, screen, text, font, *args, **kwargs):
        super(_Entry, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.screen.blit(self.Images.list_entry_base)
        self.screen.blit(self.Images.list_entry_deselected)
        entry_text = self.render_text(text)
        text_offset = self.text_offset
        self.screen.blit(entry_text, (text_offset[0], text_offset[1]))

    def click(self):
        self.screen.blit(self.Images.list_entry_selected)

    def unclick(self):
        self.screen.blit(self.Images.list_entry_deselected)


class List(MenuElement, base.FontMixin):
    """A scrollable list of _Entrys."""
    size_image = 'list_background'

    class ImageFilenames(tools.Container):
        list_background = 'general/list/list_background.png'
        list_base = 'general/list/list_base.png'
        list_scroll_handle = 'general/list/list_scroll_handle.png'

    class Alignment(object):  # Tidied up into a class here rather than keeping them all as individual variables.
        scroll_screen_dim = (747, 735)
        scroll_screen_offset = (5, 60)
        title_offset = (8, 8)

    def __init__(self, screen, title, entries, font, *args, **kwargs):
        super(List, self).__init__(screen=screen, font=font, *args, **kwargs)
        self.scrolled_amount = 0
        self.entries = []
        self.clicked_entry = None
        self.scroll_screen = None
        self.scroll_screen_view = None

        entry_size = _Entry.Images.list_entry_base.get_rect()
        self.scroll_screen = sdl.Surface((entry_size.width, entry_size.height * len(entries)))
        scroll_screen_rect = sdl.Rect(self.Alignment.scroll_screen_offset, self.Alignment.scroll_screen_dim)
        self.scroll_screen_view = self.screen.subsurface(scroll_screen_rect)

        self.scroll_screen.fill(config.MENU_BACKGROUND_COLOR)
        for i, text in enumerate(entries):
            entry_rect = sdl.Rect(0, entry_size.height * i, entry_size.width, entry_size.height)
            entry_screen = self.scroll_screen.subsurface(entry_rect)
            entry = _Entry(entry_screen, text, self.font)
            self.entries.append(entry)

        self.screen.blit(self.Images.list_base)
        self.screen.blit(self.Images.list_background)
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)
        self._update_scroll_view()

    def _update_scroll_view(self):
        """Updates how the entries are scrolled, e.g. in response to using the scroll bar."""
        self.scroll_screen_view.blit(self.scroll_screen, (0, self.scrolled_amount))

    def click(self, pos):
        screen_pos = self._screen_pos(pos)
        scroll_view_pos = self.pos_diff(screen_pos, self.Alignment.scroll_screen_offset)
        scroll_screen_pos = scroll_view_pos[0], scroll_view_pos[1] + self.scrolled_amount
        if self.clicked_entry is not None:
            self.clicked_entry.unclick()
        for i, entry in enumerate(self.entries):
            if entry.screen.point_within(scroll_screen_pos):
                clicked_index = i
                self.clicked_entry = entry
                entry.click()
                break
        else:
            clicked_index = None
            self.clicked_entry = None
        self._update_scroll_view()

        return clicked_index

    def unclick(self):
        pass
