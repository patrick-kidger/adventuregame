import collections
import Tools as tools


import Game.config.config as config

import Game.program.misc.helpers as helpers
import Game.program.misc.sdl as sdl

import Game.program.interface.base as base


class MenuElement(helpers.HasAppearances, appearance_files_location=config.INTERFACE_FOLDER):
    """Base class for all menu elements.

    When initialising menu elements, they should be passed a pygame.Surface object to use to store what the element
    currently looks like, graphically. It is expected that this will in fact be a subsurface of an overlay's screen, so
    that changes to the menu element's screen automatically get forwarded to the overlay's screen. (And is why the
    screen is passed as an initialisation argument rather than being created within __init__.)

    Menu elements may also define a tools.Container-subclass class attribute 'appearance_filenames' specifying the
    locations of the image files determining what the menu element looks like. The loaded images will then be stored in
    an attribute called 'appearances', with the same structure.

    Menu elements may define a class attribute 'size_image', which is the key corresponding to one of the loaded images,
    that will be used to determine how large the menu element is, for example when determining its alignment on the
    screen.

    Note that the position in the 'click' method is expected to be given in terms of the position of the click on the
    overall display, so self._screen_pos should be called on the position to determine the position relative to the
    screen that this element uses."""

    def __init__(self, screen, *args, **kwargs):
        super(MenuElement, self).__init__(*args, **kwargs)
        self.screen = screen
        self.on_mouseup_func = lambda menu_results, pos: (None, False)
        self.on_mousedown_func = lambda menu_results, pos: (None, False)
        self.on_un_mousedown_func = lambda menu_results: (None, False)
        self.on_mousemotion_func = lambda menu_results, pos: (None, False)
        self.on_mouseover_func = lambda menu_results, pos: (None, False)
        self.on_scroll_func = lambda menu_results, is_scroll_up, pos: (None, False)
        self.on_submit_func = lambda menu_results, pos: (None, False)
        self.on_back_func = lambda menu_results, pos: (None, False)

    def __str__(self):
        return '{cls}({{args}}) at {id_}'.format(cls=self.__class__.__name__, id_=hex(id(self)))

    def __repr__(self):
        return str(self)

    def screen_pos(self, pos):
        """Converts a position on the parent screen into a position relative to the screen used for this menu element.
        """
        subsurface_offset = self.screen.get_offset()  # If the screen is a subsurface then we need to take into account
                                                      # the offset between it and its parent surface.
        viewport_offset = self.screen.get_viewport_offset()  # If the screen is using a viewport then we also need to
                                                             # take account of that.
        total_offset = self._pos_diff(subsurface_offset, viewport_offset)
        return self._pos_diff(pos, total_offset)

    @staticmethod
    def _pos_diff(pos_a, pos_b):
        """The difference of two positions."""
        return pos_a[0] - pos_b[0], pos_a[1] - pos_b[1]

    def mousedown(self, menu_results, pos):
        """Runs when this menu element is clicked on."""
        return self.on_mousedown_func(menu_results, pos)

    def un_mousedown(self, menu_results):
        """Runs when some other menu element is clicked on; i.e. to deselect this element."""
        return self.on_un_mousedown_func(menu_results)

    def mouseup(self, menu_results, pos):
        """Runs when the mouse is released when over this menu element."""
        return self.on_mouseup_func(menu_results, pos)

    def mousemotion(self, menu_results, pos):
        """Runs when the mouse has been clicked on this element, then moved, and not yet released."""
        return self.on_mousemotion_func(menu_results, pos)

    def mouseover(self, menu_results, pos):
        """Runs when this element is moused over."""
        return self.on_mouseover_func(menu_results, pos)

    def submit(self, menu_results, pos):
        """Runs when submit-ing from this menu element."""
        return self.on_submit_func(menu_results, pos)

    def back(self, menu_results, pos):
        """Runs when back-ing from this menu element."""
        return self.on_back_func(menu_results, pos)

    def scroll(self, menu_results, is_scroll_up, pos):
        """Runs when the scroll wheel is used on this element. :is_scroll_up: should be True if the action was to scroll
        the scroll wheel upwards, and False if the action was to scroll the scroll wheel downwards."""
        return self.on_scroll_func(menu_results, is_scroll_up, pos)

    def on_scroll(self, func):
        """Registers a function to be run when scrolling on this element"""
        self.on_scroll_func = func

    def on_mousemotion(self, func):
        """Registers a function to be run when mousemotion-ing on this element"""
        self.on_mousemotion_func = func

    def on_mouseover(self, func):
        """Registers a function to be run when mouseover-ing on this element"""
        self.on_mouseover_func = func

    def on_mousedown(self, func):
        """Registers a function to be run when mousedown-ing on this element"""
        self.on_mousedown_func = func

    def on_un_mousedown(self, func):
        """Registers a function to be run when un_mousedown-ing on this element"""
        self.on_un_mousedown_func = func

    def on_mouseup(self, func):
        """Registers a function to be run when mouseup-ing on this element"""
        self.on_mouseup_func = func

    def on_submit(self, func):
        """Registers a function to be run when submit-ing from this element"""
        self.on_submit_func = func

    def on_back(self, func):
        """Registers a function to be run when back-ing on this element"""
        self.on_back_func = func


class MultipleComponentMixin(MenuElement):
    """Define a dict type '_components' attribute on the class to have it automatically pass mousedown events on to
    its components."""

    def __init__(self, **kwargs):
        super(MultipleComponentMixin, self).__init__(**kwargs)
        self._clicked_component = None

    def mousedown(self, menu_results, pos):
        clicked_component = self._find_element(pos)

        # Unclick the previous component
        if self._clicked_component is not None and self._clicked_component is not clicked_component:
            self._clicked_component.un_mousedown(menu_results)

        # Click this component
        self._clicked_component = clicked_component
        if clicked_component is not None:
            component_pos = clicked_component.screen_pos(pos)
            return clicked_component.mousedown(menu_results, component_pos)
        else:
            return super(MultipleComponentMixin, self).mousedown(menu_results, pos)

    def scroll(self, menu_results, is_scroll_up, pos):
        clicked_component = self._find_element(pos)
        if clicked_component is not None:
            component_pos = clicked_component.screen_pos(pos)
            return clicked_component.scroll(menu_results, is_scroll_up, component_pos)
        else:
            return super(MultipleComponentMixin, self).scroll(menu_results, is_scroll_up, pos)

    def mouseover(self, menu_results, pos):
        clicked_component = self._find_element(pos)
        if clicked_component is not None:
            component_pos = clicked_component.screen_pos(pos)
            return clicked_component.mouseover(menu_results, component_pos)
        else:
            return super(MultipleComponentMixin, self).mouseover(menu_results, pos)

    def mouseup(self, menu_results, pos):
        if self._clicked_component is not None:
            component_pos = self._clicked_component.screen_pos(pos)
            return self._clicked_component.mouseup(menu_results, component_pos)
        else:
            return super(MultipleComponentMixin, self).mouseup(menu_results, pos)

    def mousemotion(self, menu_results, pos):
        if self._clicked_component is not None:
            component_pos = self._clicked_component.screen_pos(pos)
            return self._clicked_component.mousemotion(menu_results, component_pos)
        else:
            return super(MultipleComponentMixin, self).mousemotion(menu_results, pos)

    def _find_element(self, pos):
        for component in self._components.values():
            if component.screen.point_within_offset(pos):
                return component
        else:
            return None


class Button(MenuElement, base.FontMixin, base.AlignmentMixin):
    """A button with text on it."""

    size_image = 'button_base'

    class appearance_filenames(tools.Container):
        button_base = 'button/button_base.png'
        button_deselect = 'button/button_deselect.png'
        button_select = 'button/button_select.png'

    def __init__(self, text, *args, **kwargs):
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])
        super(Button, self).__init__(*args, **kwargs)

        self.text = text

        self.screen.blit(self.appearances.button_base)
        self.screen.blit(self.appearances.button_deselect)
        button_text = self.render_text(text)
        text_centered = self._align(button_text.get_rect(), **align_kwargs)
        self.screen.blit(button_text, text_centered)

    def __str__(self):
        default = super(Button, self).__str__()
        return default.format(args='text={text}'.format(text=self.text))

    def mousedown(self, menu_results, pos):
        self.screen.blit(self.appearances.button_select)
        return super(Button, self).mousedown(menu_results, pos)

    def un_mousedown(self, menu_results):
        self.screen.blit(self.appearances.button_deselect)
        return super(Button, self).un_mousedown(menu_results)


class Entry(Button):
    """An entry in a List. Each entry has text on it."""

    size_image = 'button_base'

    class appearance_filenames(tools.Container):
        button_base = 'list/list_entry_base.png'
        button_deselect = 'list/list_entry_deselected.png'
        button_select = 'list/list_entry_selected.png'


class Entries(MultipleComponentMixin, MenuElement, base.FontMixin):

    horz_text_offset = 18

    def __init__(self, entry_text, *args, **kwargs):
        super(Entries, self).__init__(*args, **kwargs)

        self._components = collections.OrderedDict()

        # TODO: Handle cutout backgrounds in a better fashion
        # (having a background for a cutout, and then blitting a transparent-background surface on top, is too slow.)
        # Maybe color keys? Should then go through and use that consistently throughout, though.
        self.screen.fill((239, 228, 176))
        for count, text in enumerate(entry_text):
            entry_rect = Entry.size.move(0, Entry.size.height * count)
            entry_screen = self.screen.subsurface(entry_rect)
            entry = Entry(screen=entry_screen, text=text, font=self.font, horz_alignment=self.horz_text_offset)
            entry.on_mousedown(lambda menu_results, pos, count_=count: (count_, True))
            self._components[count] = entry

    def __str__(self):
        default = super(Entries, self).__str__()
        return default.format(args='')


class Scrollbar(MenuElement):

    class appearance_filenames(tools.Container):
        scrollbar_background = 'list/scrollbar_background.png'
        scroll_handle = 'list/list_scroll_handle.png'

    def __init__(self, scrollable, **kwargs):
        super(Scrollbar, self).__init__(**kwargs)

        self.scrollable = scrollable
        self._scrolling = False

        # To put the middle, not the top, of the handle where the user's cursor is.
        scroll_handle_height = self.appearances.scroll_handle.get_rect().height
        self._scroll_handle_offset = scroll_handle_height // 2
        # The height of the scrollbar
        scroll_height = self.appearances.scrollbar_background.get_rect().height
        # The scrollable amount (slightly smaller than the scroll_height because the scroll handle takes up space)
        self.clamp_length = scroll_height - scroll_handle_height
        # The rect for where the scroll handle currently is.
        self.scroll_handle_rect = None

        self.move(0)

    def __str__(self):
        default = super(Scrollbar, self).__str__()
        return default.format(args='scrollable={scrollable}'.format(scrollable=self.scrollable))

    def move(self, pos):
        pos_ = tools.clamp(pos - self._scroll_handle_offset, 0, self.clamp_length)
        self.screen.blit(self.appearances.scrollbar_background)
        self.scroll_handle_rect = self.screen.blit(self.appearances.scroll_handle, (0, pos_))
        return pos_

    def mousedown(self, menu_results, pos):
        if self.scroll_handle_rect.collidepoint(pos):
            self._scrolling = True
        else:
            self._scrolling = False
        return super(Scrollbar, self).mousedown(menu_results, pos)

    def mouseup(self, menu_results, pos):
        self._scrolling = False
        return super(Scrollbar, self).mouseup(menu_results, pos)

    def mousemotion(self, menu_results, pos):
        if self._scrolling:
            # Move the scroll handle
            scroll_handle_pos = self.move(pos[1])

            # Move the entries
            excess_height = max(0, self.scrollable.screen.get_height() - self.scrollable.screen.viewport.height)
            entries_offset = (excess_height * scroll_handle_pos) / self.clamp_length

            self.scrollable.screen.viewport.top = entries_offset
        return super(Scrollbar, self).mousemotion(menu_results, pos)

    def scroll(self, menu_results, is_scroll_up, pos):
        if not self._scrolling:
            excess_height = self.scrollable.screen.get_height() - self.scrollable.screen.viewport.height
            if excess_height > 0:
                moved_list_pos = self.scrollable.screen.viewport.top + {True: -1, False: 1}[is_scroll_up] * config.SCROLL_SPEED
                self.scrollable.screen.viewport.top = tools.clamp(moved_list_pos, 0, excess_height)
                moved_scrollbar_pos = (self.scrollable.screen.viewport.top * self.scrollable.screen.viewport.height) / excess_height
                self.move(moved_scrollbar_pos)
        return super(Scrollbar, self).scroll(menu_results, is_scroll_up, pos)


class List(MultipleComponentMixin, MenuElement, base.FontMixin):
    """A scrollable list of entries."""

    size_image = 'list_background'

    class appearance_filenames(tools.Container):
        list_background = 'list/list_background.png'

    class Alignment:  # Tidied up into a class here rather than keeping them all as individual variables.
        entry_cutout = sdl.Rect((5, 60), (747, 735))  # Cutout in the main screen for entries
        entry_view = sdl.Rect((0, 0), (747, 735))     # View of the entries screen

        scrollbar_rect = sdl.Rect((757, 60), (38, 735))  # Cutout in the main screen for the scrollbar

        title_offset = (8, 8)

    def __init__(self, title, entry_text, **kwargs):
        super(List, self).__init__(**kwargs)

        self._components = tools.Object()  # Used with MultipleComponentMixin; the components making up this list
        self.title = title

        # Set up what the 'background' images for the list are doing
        self.screen.blit(self.appearances.list_background)
        title_text = self.render_text(title)
        self.screen.blit(title_text, self.Alignment.title_offset)

        # The surface we'll put the entries on
        entry_size = Entry.size
        self.entry_view = sdl.Surface((entry_size.width, entry_size.height * len(entry_text)),
                                      viewport=self.Alignment.entry_view)
        self.screen.cutout(location=self.Alignment.entry_cutout, target=self.entry_view)
        # The surface we'll put the scrollbar on
        scrollbar_screen = self.screen.subsurface(self.Alignment.scrollbar_rect)

        # Record the components making up this menu element
        self._components.entries = Entries(screen=self.entry_view, font=self.font, entry_text=entry_text)
        self._components.scrollbar = Scrollbar(screen=scrollbar_screen, scrollable=self._components.entries)

    def __str__(self):
        default = super(List, self).__str__()
        return default.format(args='title={title}'.format(title=self.title))

    def scroll(self, menu_results, is_scroll_up, pos):
        return self._components.scrollbar.scroll(menu_results, is_scroll_up, pos)


class MessageBox(MultipleComponentMixin, MenuElement, base.FontMixin):
    """A message box."""

    size_image = 'messagebox_background'

    class appearance_filenames(tools.Container):
        messagebox_background = 'messagebox/messagebox_background.png'

    class Alignment:
        title_offset = (8, 8)
        text_offset = (8, 63)
        line_length = 32
        max_lines = 4
        button_rect = sdl.Rect((0, 211), (400, 60))

    def __init__(self, title, text, buttons, **kwargs):
        if len(buttons) != 1:
            # TODO: Obviously, add support for multiple buttons...
            raise Exception('Currently only supports having a single button!')
        super(MessageBox, self).__init__(**kwargs)

        self._components = tools.Object()
        self.title = title

        self.screen.blit(self.appearances.messagebox_background)
        title_text = self.render_text(title)
        sliced_text = list(tools.slice_pieces(text, self.Alignment.line_length))[:self.Alignment.max_lines]
        text = self.render_text_with_newlines(sliced_text)
        self.screen.blit(title_text, self.Alignment.title_offset)
        self.screen.blit(text, self.Alignment.text_offset)

        button_screen = self.screen.subsurface(self.Alignment.button_rect)
        # TODO: Have a better way of doing this fill, as well.
        button_screen.fill((195, 195, 195))
        for button in buttons:
            self._components[button] = Button(screen=button_screen, text=button, font=self.font)

    def __str__(self):
        default = super(MessageBox, self).__str__()
        return default.format(args='title={title}'.format(title=self.title))

    def on_mouseup_button(self, button, func):
        self._components[button].on_mouseup(func)
