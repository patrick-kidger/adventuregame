import Tools as tools


import Game.config.config as config
import Game.config.strings as strings

import Game.program.misc.commands as commands
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl

import Game.program.interface.base as base


class TextOverlay(base.BaseOverlay, base.FontMixin):
    """Handles outputting text to the screen."""

    def reset(self):
        self.text = ''
        self.flush = True
        super(TextOverlay, self).reset()

    def handle(self, event):
        if sdl.event.is_key(event):
            self.output(event.unicode)
        else:
            raise exceptions.UnhandledInput

    def output(self, output_val, width=None, max_text_width=None, end='', **kwargs):
        """Outputs text.

        :str output_val: The string to output.
        :int width: Optional. The text that is enterd on this __call__ with be padded to this width.
        :int max_text_width: Optional. The overall text width will be line-wrapped to this.
        :str end: Added to output_val (after setting its width) to produce the overall string that is being added. It's
            mostly here to mimic the 'end' argument that the built-in print function allows."""

        if width is not None:
            output_val = '{{:{}}}'.format(width).format(output_val)
        output_val += end
        self.text += output_val

        if self.flush:
            self.flush_output()

    def flush_output(self):
        # Handle backspaces
        self.text = tools.re_sub_recursive(r'[^\x08]\x08', '', self.text)  # \x08 = backspace. \b doesn't work.
        self.text.lstrip('\b')

        text_with_newlines = []
        split_text = self.text.split('\n')
        for line in split_text:
            text_with_newlines.extend(list(tools.slice_pieces(line, config.CONSOLE_LINE_LENGTH)))

        self.wipe()

        text = self.render_text_with_newlines(text_with_newlines, background=self.background_color)
        self.screen.blit(text, (0, self._screen_height - text.get_rect().height))

    def bulk_output(self):
        return tools.set_context_variables(self, ('flush',), False, self.flush_output)

    def sep(self, length, **kwargs):
        """Outputs a separator of the given length."""
        self.output(strings.Sep.SEP * length, **kwargs)

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

        with self.bulk_output():
            self.output(strings.Sep.DR_SEP)
            self.sep(overall_width)
            self.output(strings.Sep.DL_SEP, end='\n')
            self.output(strings.Sep.UD_SEP)
            self.output(edge_space + title + edge_space, width=overall_width)
            self.output(strings.Sep.UD_SEP, end='\n')
            self.output(strings.Sep.UDR_SEP)
            self.sep(overall_width)
            self.output(strings.Sep.UDL_SEP, end='\n')
            if headers is not None:
                self.output(strings.Sep.UD_SEP)
                for header, column_width in zip(headers, column_widths):
                    self.output(edge_space)
                    self.output(header, width=column_width)
                    self.output(edge_space)
                    self.output(strings.Sep.UD_SEP)
                self.output('\n')
                self.output(strings.Sep.UD_SEP)
                for column_width in column_widths[:-1]:
                    self.sep(column_width)
                    self.output(strings.Sep.UDLR_SEP)
                self.sep(column_widths[-1])
                self.output(strings.Sep.UD_SEP, end='\n')
            for row in rows:
                self.output(strings.Sep.UD_SEP)
                for entry, column_width in zip(row, column_widths):
                    self.output(edge_space)
                    self.output(entry, width=column_width)
                    self.output(edge_space)
                    self.output(strings.Sep.UD_SEP)
                self.output('\n')
            self.output(strings.Sep.UR_SEP)
            self.sep(overall_width)
            self.output(strings.Sep.UL_SEP, end='\n')


class DebugOverlay(TextOverlay):
    def __init__(self, **kwargs):
        self._screen_enabled = False
        super(DebugOverlay, self).__init__(**kwargs)

    @property
    def screen_enabled(self):
        return self._screen_enabled

    @screen_enabled.setter
    def screen_enabled(self, value):
        if value:
            sdl.event.set_grab(False)
        else:
            sdl.event.set_grab(True)
        self._screen_enabled = value

    def reset(self, prompt=True):
        super(DebugOverlay, self).reset()
        self.command_memory = tools.nonneg_deque([], config.CONSOLE_MEMORY_SIZE)
        self.command_memory_cursor = -1
        self.current_command = ''
        if prompt:
            self.output(config.CONSOLE_PROMPT)

    def handle(self, event):
        if sdl.event.is_key(event):
            if event.key in (sdl.K_UP, sdl.K_DOWN):
                k_i = {sdl.K_UP: 1, sdl.K_DOWN: -1}
                moved_text_memory_cursor = tools.clamp(self.command_memory_cursor + k_i[event.key],
                                                       -1, config.CONSOLE_MEMORY_SIZE)
                try:
                    text_from_memory = self.command_memory[moved_text_memory_cursor]
                except IndexError:
                    pass
                else:
                    self.output('\b' * len(self.current_command))
                    self.current_command = text_from_memory
                    self.command_memory_cursor = moved_text_memory_cursor
                    self.output(self.current_command)
            else:
                self.command_memory_cursor = -1

                if event.key in sdl.K_ENTER:
                    if self.current_command != '':
                        self.command_memory.appendleft(self.current_command)
                    self.output('\n')
                    self._debug_command()
                    self.current_command = ''
                    self.output(config.CONSOLE_PROMPT)
                elif event.key == sdl.K_ESCAPE:
                    self.output.enabled = False
                    self.disable_listener()
                elif event.key == sdl.K_BACKSPACE:
                    if self.current_command != '':
                        super(DebugOverlay, self).handle(event)
                        self.current_command = self.current_command[:-1]
                else:
                    super(DebugOverlay, self).handle(event)
                    self.current_command += event.unicode
        else:
            raise exceptions.UnhandledInput

    def _debug_command(self):
        """Finds and executes the debug command corresponding to currently stored text."""
        command_split = self.current_command.strip().split(' ')
        command_name = command_split[0]
        command_args = tools.qlist(command_split[1:], except_val='')
        try:
            command = commands.get_command(command_name)
        except KeyError:
            self._invalid_input()
        else:
            print_result = command.do(self._game_instance, command_args)
            if print_result is not None:
                self.output(print_result, end='\n')

    def _invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.output(strings.Debug.INVALID_INPUT, end='\n')
