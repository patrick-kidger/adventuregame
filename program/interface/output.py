import Tools as tools


import config.config as config
import config.internal_strings as internal_strings
import config.strings as strings

import program.interface.base as base
import program.interface.menu_elements as menu_elements

import program.misc.exceptions as exceptions
import program.misc.helpers as helpers
import program.misc.sdl as sdl


class BaseOverlay(base.BaseIO, helpers.EnablerMixin, helpers.NameMixin):
    """Abstract base class for all overlays. An 'overlay' is a layer on the screen that may be outputted to."""
    default_output_kwargs = {}

    def __init__(self, name, location, size, background_color, *args, **kwargs):
        self.location = location
        self.screen = sdl.Surface(size)
        self.background_color = background_color

        self.reset()

        super(BaseOverlay, self).__init__(name=name, enabled=False, *args, **kwargs)

    def __call__(self, output_val, flush=False):
        # Just a convenience, to allow for just calling with flush=True as an argument, rather than putting an
        # output.flush() on the next line.
        if flush:
            self.flush()

    def clear(self, flush=False):
        """Clears the overlay of everything that has been printed to it."""
        self.wipe(flush)
        self.reset()

    def wipe(self, flush=False):
        """Fills the overlay with its background color."""
        self.screen.fill(self.background_color)
        if flush:
            self.flush()

    def reset(self):
        """Resets all extra data associated with this overlay."""

    def flush(self):
        self.out.flush(self.name)


class GraphicsOverlay(BaseOverlay):
    """Handles outputting graphics to the screen."""


class MenuOverlay(GraphicsOverlay, base.FontMixin):
    """A graphics overlay for menus."""
    def reset(self):
        self.menu_elements = {}

    def list(self, title, entries, horz_alignment=internal_strings.Alignment.CENTER, vert_alignment=internal_strings.Alignment.CENTER):
        list_screen = self._align(menu_elements.List.size, horz_alignment, vert_alignment)
        created_list = menu_elements.List(list_screen, title, entries, self.font)
        return created_list

    def submit(self, text, horz_alignment=internal_strings.Alignment.RIGHT, vert_alignment=internal_strings.Alignment.BOTTOM):
        submit_button = self.button(text, horz_alignment, vert_alignment)
        # TODO
        return submit_button

    def button(self, text, horz_alignment=internal_strings.Alignment.CENTER, vert_alignment=internal_strings.Alignment.CENTER):
        button_screen = self._align(menu_elements.Button.size, horz_alignment, vert_alignment)
        created_button = menu_elements.Button(button_screen, text, self.font)
        return created_button

    def _align(self, image_rect, horz_alignment=internal_strings.Alignment.CENTER, vert_alignment=internal_strings.Alignment.CENTER):
        screen_rect = self.screen.get_rect()
        if horz_alignment == internal_strings.Alignment.LEFT:
            horz_pos = 0
        elif horz_alignment == internal_strings.Alignment.RIGHT:
            horz_pos = screen_rect.width - image_rect.width
        elif horz_alignment == internal_strings.Alignment.CENTER:
            horz_pos = (screen_rect.width - image_rect.width) // 2
        else:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.BAD_ALIGNMENT.format(alignment=horz_alignment))

        if vert_alignment == internal_strings.Alignment.TOP:
            vert_pos = 0
        elif vert_alignment == internal_strings.Alignment.LEFT:
            vert_pos = screen_rect.height - image_rect.height
        elif vert_alignment == internal_strings.Alignment.CENTER:
            vert_pos = (screen_rect.height - image_rect.height) // 2
        else:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.BAD_ALIGNMENT.format(alignment=vert_alignment))

        image_rect = sdl.Rect(horz_pos, vert_pos, image_rect.width, image_rect.height)
        return self.screen.subsurface(image_rect)


class TextOverlay(BaseOverlay, base.FontMixin):
    """Handles outputting text to the screen."""

    def __call__(self, output_val, width=None, end='', **kwargs):
        """Outputs text.

        :str outputstr: The string to output.
        :int width: Optional. The text with be padded to this width."""

        if width is not None:
            output_val = '{{:{}}}'.format(width).format(output_val)
        output_val += end
        self.text += output_val
        # \x08 = backspace. \b doesn't work for some reason.
        self.text = helpers.re_sub_recursive(r'[^\x08]\x08', '', self.text)
        self.text.lstrip('\b')

        self.wipe()

        split_text = self.text.split('\n')
        text_cursor = (0, 0)
        for output_text in split_text:
            text = self.render_text(output_text)
            text_area = self.screen.blit(text, text_cursor)
            text_cursor = (0, text_area.bottom)
        super(TextOverlay, self).__call__(output_val, **kwargs)

    def reset(self):
        self.text = ''

    def sep(self, length, **kwargs):
        """Prints a separator of the given length."""
        self(strings.Sep.SEP * length, **kwargs)

    def table(self, title, columns, headers=None, edge_space=''):
        """Prints a table in text.

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
        sdl.display.set_caption(config.WINDOW_NAME)
        super(Output, self).__init__(*args, **kwargs)

    def register_interface(self, interface):
        for overlay in self.overlays.values():
            overlay.register_interface(interface)
        super(Output, self).register_interface(interface)

    def flush(self, overlay_names=None):
        """Pushes the changes from the overlays to the main screen.

        :str or tuple[str] overlay_names: The names of the overlays to update."""
        updated_areas = []
        if overlay_names is None:
            overlays = self.overlays.values()
        else:
            if isinstance(overlay_names, str):
                overlay_names = (overlay_names,)
            overlays = tuple(self.overlays[overlay_name] for overlay_name in overlay_names)

        for overlay in overlays:
            if overlay.enabled:
                updated_area = self.screen.blit(overlay.screen, overlay.location)
                updated_areas.append(updated_area)

        sdl.display.update(updated_areas)
