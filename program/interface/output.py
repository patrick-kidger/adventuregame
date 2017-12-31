import collections
import Tools as tools


import Game.config.config as config
import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.interface.base as base
import Game.program.interface.menu_elements as menu_elements
import Game.program.misc.helpers as helpers
import Game.program.misc.sdl as sdl


class BaseOverlay(base.BaseIO, helpers.EnablerMixin):
    """Abstract base class for all overlays. An 'overlay' is a layer on the screen that may be outputted to. An instance
    of the 'Output' class keeps track of the different overlays.

    Each overlay has a location on the main display screen that is sends graphical information to, and a screen that it
    copies the graphical information from. Overlays are by default disabled, meaning that they will not send graphical
    information to the main display screen. They must be enabled before they will do so.

    Overlays should define a __call__(...) method through which they are called to output graphical information to their
    screen. They may also define a reset(self) method which will be called to return the instance to the state it
    was initialised in. Overlays should put those attributes they need resetting here."""

    def __init__(self, name, location, size, background_color, *args, **kwargs):
        super(BaseOverlay, self).__init__(enabled=False, *args, **kwargs)
        self.name = name
        self.location = location
        self.screen = sdl.Surface(size)
        self.background_color = background_color

        self.reset()

    def reset(self):
        """Resets all extra data associated with this overlay."""
        self.wipe()
        # Endpoint for super calls.

    # Subclasses definitions of __call__ will likely involve setting required arguments, which obviously violates LSP.
    # Still this seems like the best solution. The alternative would be to demand that all __call__ definitions finish
    # with a super call to some _call function on this base class implementing the below function, which just seems even
    # worse.
    def __call__(self):
        pass
        # Endpoint for super calls.

    def wipe(self):
        """Fills the overlay with its background color."""
        self.screen.fill(self.background_color)


class GraphicsOverlay(BaseOverlay):
    """Handles outputting graphics to the screen."""

    def __call__(self, source, dest=(0, 0), area=None, special_flags=0, offset=None, *args, **kwargs):
        if offset is not None:
            dest = dest[0] - offset.x, dest[1] - offset.y
        self.screen.blit_offset(source, dest, area, special_flags)
        super(GraphicsOverlay, self).__call__(*args, **kwargs)


class MenuOverlay(GraphicsOverlay, base.FontMixin, helpers.AlignmentMixin):
    """A graphics overlay for menus. This overlay is rather special, in that it does not define a __call__ method.
    Instead it provides methods for placing menu elements on the screen. Subsequently making a call to an associated
    menu listener will then determine which of these menu elements are interacted with."""

    def reset(self):
        self.screen.clear_cutouts()
        self.menu_elements = collections.deque()  # All menu elements
        self.necessary_elements = set()  # Those elements which must have non-None data set before the menu can be
                                         # 'submitted', i.e. pass data back to the game.
        self.submit_elements = set()     # Those elements which, when interacted with, will attempt to 'submit' the
                                         # current menu.
        self.back_elements = set()       # As submit_elements, but do not require the necessary elements to have
                                         # non-None data to submit. (i.e. for returning to earlier menus)
        super(MenuOverlay, self).reset()

    def remove(self, element):
        self.screen.discard_cutout(element.screen)
        self.menu_elements.remove(element)
        self.necessary_elements.discard(element)
        self.submit_elements.discard(element)
        self.back_elements.discard(element)

    def list(self, title, entry_text, necessary=False, **kwargs):
        """Creates a list with the given title, entries, and alignment.

        :str title: The title to put at the top of the list.
        :iter[str] entries: The entries to put in the list.
        :bool necessary: Optional argument determining whether or not this element must have non-None data set before
            the menu can be submitted. If not passed, defaults to False..
        :str horz_alignment: Optional argument. An internal.Alignment attribute defining the horizontal
            placement of the list on the overlay's screen. If not passed, defaults to the center of the screen.
        :str vert_alignment: Optional argument. As horz_alignment, for vertical placement. If not passed, defaults to
            the center of the screen.
        """
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])

        list_screen = sdl.Surface.from_rect(menu_elements.List.size)
        list_screen.fill(self.background_color)
        self._view_cutout(list_screen, **align_kwargs)
        created_list = menu_elements.List(screen=list_screen, title=title, entry_text=entry_text, font=self.font)
        self.menu_elements.appendleft(created_list)
        if necessary:
            self.necessary_elements.add(created_list)
        return created_list

    def messagebox(self, title, text, buttons=(strings.Menus.OK,), **kwargs):
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])
        messagebox_screen = sdl.Surface.from_rect(menu_elements.MessageBox.size)
        messagebox_screen.fill(self.background_color)
        self._view_cutout(messagebox_screen, **align_kwargs)
        created_messagebox = menu_elements.MessageBox(screen=messagebox_screen, title=title, text=text, buttons=buttons,
                                                      font=self.font)
        self.menu_elements.appendleft(created_messagebox)
        return created_messagebox

    def button(self, text, necessary=False, **kwargs):
        """Creates a button with the given text.

        :str text: The text to put on the button.
        :press: The value that is returned when this button is pressed
        :bool necessary: As in the method 'list'.
        :str horz_alignment: As in the method 'list'.
        :str vert_alignment: As in the method 'list'.
        """
        # Not specified as arguments above so that they automatically use the default argument values in self._view
        align_kwargs = tools.extract_keys(kwargs, ['horz_alignment', 'vert_alignment'])

        button_screen = sdl.Surface.from_rect(menu_elements.Button.size)
        button_screen.fill(self.background_color)
        self._view_cutout(button_screen, **align_kwargs)
        created_button = menu_elements.Button(screen=button_screen, text=text, font=self.font)
        self.menu_elements.appendleft(created_button)
        if necessary:
            self.necessary_elements.add(created_button)
        return created_button

    def submit(self, text, horz_alignment=internal.Alignment.RIGHT,
               vert_alignment=internal.Alignment.BOTTOM):
        """Creates a submit button with the given text - pressing this button will attempt to submit the menu.

        :str text: The text to put on the submit button.
        :str horz_alignment: As in the method 'list', but defaults to the right.
        :str vert_alignment: As in the method 'list', but defaults to the bottom."""
        submit_button = self.button(text, horz_alignment=horz_alignment, vert_alignment=vert_alignment)
        self.submit_elements.add(submit_button)
        return submit_button

    def back(self, text, horz_alignment=internal.Alignment.LEFT,
             vert_alignment=internal.Alignment.BOTTOM):
        """Creates a back button with the given text - pressing this button is a submit button, as above, but that
        does not require necessary elements to have data."""
        back_button = self.button(text, horz_alignment=horz_alignment, vert_alignment=vert_alignment)
        self.back_elements.add(back_button)
        return back_button


class TextOverlay(BaseOverlay, base.FontMixin):
    """Handles outputting text to the screen."""

    def __init__(self, *args, **kwargs):
        super(TextOverlay, self).__init__(*args, **kwargs)
        self._screen_height = self.screen.get_rect().height

    def reset(self):
        self.previous_lines = []
        self.text = ''
        super(TextOverlay, self).reset()

    def __call__(self, output_val, width=None, max_text_width=None, end='', **kwargs):
        """Outputs text.

        :str output_val: The string to output.
        :int width: Optional. The text that is enterd on this __call__ with be padded to this width.
        :int max_text_width: Optional. The overall text width will be line-wrapped to this.
        :str end: Added to output_val (after setting its width) to produce the overall string that is being added. It's
            mostly here to mimic the 'end' argument that the built-in print function allows."""

        if width is not None:
            output_val = '{{:{}}}'.format(width).format(output_val)
        output_val += end
        text = self.text + output_val

        # Handle backspaces
        text = tools.re_sub_recursive(r'[^\x08]\x08', '', text)  # \x08 = backspace. \b doesn't work.
        text.lstrip('\b')

        new_previous_lines = []
        split_text = text.split('\n')
        for line in split_text:
            new_previous_lines.extend(list(tools.slice_pieces(line, config.CONSOLE_LINE_LENGTH)))
        self.previous_lines.extend(new_previous_lines[:-1])
        self.text = new_previous_lines[-1]

        self.wipe()

        text = self.render_text_with_newlines(self.previous_lines + [self.text], background=self.background_color)
        self.screen.blit(text, (0, self._screen_height - text.get_rect().height))
        super(TextOverlay, self).__call__(**kwargs)

    def sep(self, length, **kwargs):
        """Outputs a separator of the given length."""
        self(strings.Sep.SEP * length, **kwargs)

    def table(self, title, columns, headers=None, edge_space=''):
        """Outputs a table in text.

        :str title: A title to put at the top of the table
        :iter[iter] columns: The component iterables should be the data to put in the columns. Each component iterable
            should be the same length.
        :iter[str] headers: Optional. The name of each column. This iter should have the same length as :columns:.
        :str edge_space: Optional. Any horizontal spacing to put around each element of the table.
        """

        if headers is None:
            header_names = ['' for _ in range(len(columns))]
        else:
            header_names = headers
        column_widths = []
        # In case we're passed generators that get consumed
        columns = [list(column) for column in columns]
        for column, header in zip(columns, header_names):
            column_width = len(header)
            for column_entry in column:
                column_width = max(column_width, len(column_entry))
            column_widths.append(column_width)
        overall_title_width = len(title) + len(
            edge_space) * 2  # The width of the header text, plus space to either side of it
        overall_column_width = (sum(column_widths) +  # The width of the columns
                                len(column_widths) * len(
                                    edge_space) * 2 +  # The width of the space either side of the entry in each column
                                (len(column_widths) - 1) * len(
                                    strings.Sep.VERT_SEP))  # The width of the lines separating columns
        overall_width = max(overall_title_width, overall_column_width)
        if overall_title_width > overall_column_width:
            column_widths[-1] += overall_title_width - overall_column_width

        rows = zip(*columns)

        self(strings.Sep.DR_SEP)
        self.sep(overall_width)
        self(strings.Sep.DL_SEP, end='\n')
        self(strings.Sep.UD_SEP)
        self(edge_space + title + edge_space, width=overall_width)
        self(strings.Sep.UD_SEP, end='\n')
        self(strings.Sep.UDR_SEP)
        self.sep(overall_width)
        self(strings.Sep.UDL_SEP, end='\n')
        if headers is not None:
            self(strings.Sep.UD_SEP)
            for header, column_width in zip(headers, column_widths):
                self(edge_space)
                self(header, width=column_width)
                self(edge_space)
                self(strings.Sep.UD_SEP)
            self('\n')
            self(strings.Sep.UD_SEP)
            for column_width in column_widths[:-1]:
                self.sep(column_width)
                self(strings.Sep.UDLR_SEP)
            self.sep(column_widths[-1])
            self(strings.Sep.UD_SEP, end='\n')
        for row in rows:
            self(strings.Sep.UD_SEP)
            for entry, column_width in zip(row, column_widths):
                self(edge_space)
                self(entry, width=column_width)
                self(edge_space)
                self(strings.Sep.UD_SEP)
            self('\n')
        self(strings.Sep.UR_SEP)
        self.sep(overall_width)
        self(strings.Sep.UL_SEP, end='\n')


class Output(base.BaseIO):
    """The overall output. It takes its various overlays and then combines them to produce output to the screen."""

    def __init__(self, overlays, *args, **kwargs):
        self.overlays = overlays
        self.screen = sdl.display.set_mode(config.SCREEN_SIZE)
        self.screen_size = self.screen.get_rect()
        sdl.display.set_caption(config.WINDOW_NAME)
        super(Output, self).__init__(*args, **kwargs)

    def reset(self, overlay_to_reset=None):
        """Resets the output back to its initial state. If passed an argument, it will instead reset just that overlay.
        """
        if overlay_to_reset is None:
            for overlay in self.overlays.values():
                overlay.reset()
                overlay.disable()
        else:
            self.overlays[overlay_to_reset].reset()

    def register_interface(self, interface):
        for overlay in self.overlays.values():
            overlay.register_interface(interface)
        super(Output, self).register_interface(interface)

    def flush(self):
        """Pushes the changes from the overlays to the main screen."""
        for overlay in self.overlays.values():
            if overlay.enabled:
                overlay.screen.update_cutouts()
                self.screen.blit(overlay.screen, overlay.location)

        sdl.display.update()

    def use(self, overlay_name):
        """Temporarily enable the specified overlay. For use in 'with' statements."""
        return self.overlays[overlay_name].use()
