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
                                                             # take account of that.
        total_offset = _pos_diff(subsurface_offset, viewport_offset)
        return _pos_diff(pos, total_offset)

    def point_within(self, pos):
        """Whether or not the given point is within the boundaries of this menu component."""
        return self.screen.point_within(pos)

    def mousedown(self, pos):
        """Runs when this menu element is clicked on."""

    def un_mousedown(self):
        """Runs when some other menu element is clicked on; i.e. to deselect this element."""

    def mouseup(self, pos):
        """Runs when the mouse is released when over this menu element."""

    def mousemotion(self, pos):
        """Runs when this element is moused over."""


class MultipleComponentMixin(object):
    def mousedown(self, pos):
        for count, component in enumerate(self._components.values()):
            if component.point_within(pos):
                component_pos = component.screen_pos(pos)
                click_result = component.mousedown(component_pos)
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

    def mousedown(self, pos):
        self.screen.blit(self.Images.button_select)

    def un_mousedown(self):
        self.screen.blit(self.Images.button_deselect)


class Entry(Button):
    """An entry in a List. Each entry has text on it."""

    class ImageFilenames(tools.Container):
        button_base = 'general/list/list_entry_base.png'
        button_deselect = 'general/list/list_entry_deselected.png'
        button_select = 'general/list/list_entry_selected.png'


class Entries(MultipleComponentMixin, MenuElement, base.FontMixin):

    horz_text_offset = 18

    def __init__(self, entry_text, entry_size, *args, **kwargs):
        super(Entries, self).__init__(*args, **kwargs)
        # TODO: Handle cutout backgrounds in a better fashion
        # (having a background for a cutout, and then blitting a transparent-background surface on top, is too slow.)
        # Maybe color keys? Should then go through and use that consistently throughout, though.
        self.screen.fill((239, 228, 176))

        self._components = collections.OrderedDict()
        self.clicked_entry = None

        for count, text in enumerate(entry_text):
            entry_rect = sdl.Rect(0, entry_size.height * count, entry_size.width, entry_size.height)
            entry_screen = self.screen.subsurface(entry_rect)
            entry = Entry(screen=entry_screen, text=text, font=self.font, horz_alignment=self.horz_text_offset)
            self._components[count] = entry


class Scrollbar(MenuElement):

    class ImageFilenames(tools.Container):
        scrollbar_background = 'general/list/scrollbar_background.png'
        scroll_handle = 'general/list/list_scroll_handle.png'

    def __init__(self, *args, **kwargs):
        # To put the middle, not the top, of the handle where the user's cursor is.
        scroll_handle_height = self.Images.scroll_handle.get_rect().height
        self._scroll_handle_offset = scroll_handle_height // 2
        # The height of the scrollbar
        self.scroll_length = self.Images.scrollbar_background.get_rect().height
        # The scrollable amount (slightly smaller than the scroll_length because the scroll handle takes up space)
        self.clamp_length = self.scroll_length - scroll_handle_height

        # The rect for where the scroll handle currently is.
        self.scroll_handle_rect = None

        super(Scrollbar, self).__init__(*args, **kwargs)
        self.move(0)

    def move(self, pos):
        pos_ = tools.clamp(pos - self._scroll_handle_offset, 0, self.clamp_length)
        self.screen.blit(self.Images.scrollbar_background)
        self.scroll_handle_rect = self.screen.blit(self.Images.scroll_handle, (0, pos_))
        return pos_


class List(MultipleComponentMixin, MenuElement, base.FontMixin):
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
        self._clicked_entry = None  # The currently selected element from the list
        self._clicked_entry_index = None  # The index of the currently selected element in the list
        self._scrolling = False  # Whether we are currently scrolling the list
        self._components = tools.Object()  # Used with MultipleComponentMixin; the components making up this list

        super(List, self).__init__(font=font, *args, **kwargs)
        # Set up what the 'background' images for the list are doing
        self.screen.blit(self.Images.list_background)
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)

        # The surface we'll put the entries on
        self.entry_view = sdl.Surface((self.Alignment.entry_size.width,
                                       self.Alignment.entry_size.height * len(entry_text)),
                                      viewport=self.Alignment.entry_view)
        self.screen.cutout(location=self.Alignment.entry_cutout, target=self.entry_view)
        # The surface we'll put the scrollbar on
        scrollbar_screen = self.screen.subsurface(self.Alignment.scrollbar_cutout)

        # Record the components making up this menu element
        self._components.entries = Entries(screen=self.entry_view, font=font, entry_text=entry_text,
                                           entry_size=self.Alignment.entry_size)
        self._components.scrollbar = Scrollbar(screen=scrollbar_screen)

        self._update_scroll_view()

    def _update_scroll_view(self):
        """Updates how the entries are scrolled, e.g. in response to using the scroll bar."""
        self.screen.update_cutouts()

    def mousedown(self, pos):
        click_result = super(List, self).mousedown(pos)
        if click_result.component is self._components.scrollbar:
            pos_rel_to_scrollbar = self._components.scrollbar.screen_pos(pos)
            if self._components.scrollbar.scroll_handle_rect.collidepoint(pos_rel_to_scrollbar):
                self._scrolling = True
            else:
                self._scrolling = False
        else:
            self._scrolling = False

        if click_result.component is self._components.entries:
            if self._clicked_entry is not None:
                self._clicked_entry.un_mousedown()
            self._clicked_entry = click_result.click_result.component
            self._clicked_entry_index = click_result.click_result.count

        self._update_scroll_view()
        return self._clicked_entry_index

    def mouseup(self, pos):
        self._scrolling = False

    def mousemotion(self, pos):
        if self._scrolling:
            # Move the scroll handle
            pos_rel_to_scrollbar = self._components.scrollbar.screen_pos(pos)
            scroll_handle_pos = self._components.scrollbar.move(pos_rel_to_scrollbar[1])

            # Move the entries
            excess_length = max(0, self.entry_view.get_height() - self._components.scrollbar.scroll_length)
            entries_offset = (excess_length * scroll_handle_pos) / self._components.scrollbar.clamp_length

            viewport = self.entry_view.get_viewport()
            viewport.top = entries_offset
            self.entry_view.set_viewport(viewport)
            self._update_scroll_view()
