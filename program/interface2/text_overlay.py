import Tools as tools


import Game.config.config as config
import Game.config.strings as strings

import Game.program.interface.base as base
import Game.program.interface2.base_overlay as base_overlay
import Game.program.misc.commands as commands
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class TextOverlay(base_overlay.BaseOverlay, base.FontMixin):
    """Handles outputting text to the screen."""

    def __init__(self, *args, **kwargs):
        super(TextOverlay, self).__init__(*args, **kwargs)
        self._screen_height = self.screen.get_rect().height

    def reset(self):
        self.previous_lines = []
        self.text = ''
        self.editable_text = ''
        super(TextOverlay, self).reset()

    def handle(self, event):
        if sdl.event.is_key(event):
            should_output = True
            if event.key == sdl.K_BACKSPACE:
                # Disable outputting backspaces if we're not actually modifying the text with them.
                if len(self.editable_text) == 0:
                    should_output = False
                self.editable_text = self.editable_text[:-1]
            else:
                self.editable_text += event.unicode

            if should_output:
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
    def __init__(self, *args, **kwargs):
        super(DebugOverlay, self).__init__(*args, **kwargs)
        self.command_memory = tools.nonneg_deque([], config.CONSOLE_MEMORY_SIZE)
        self.command_memory_cursor = -1

    def reset(self):
        super(DebugOverlay, self).reset()
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
                    self.output('\b' * len(self.editable_text))
                    self.editable_text = text_from_memory
                    self.command_memory_cursor = moved_text_memory_cursor
                    self.output(self.editable_text)
            else:
                self.command_memory_cursor = -1

                if event.key in sdl.K_ENTER:
                    if self.editable_text != '':
                        self.command_memory.appendleft(self.editable_text)
                    self.output('\n')
                    self._debug_command()
                elif event.key == sdl.K_ESCAPE:
                    self.output.enabled = False
                    self.disable_listener()
                else:
                    super(DebugOverlay, self).handle(event)
        else:
            raise exceptions.UnhandledInput

    def _debug_command(self):
        """Finds and executes the debug command corresponding to currently stored text."""
        command_split = self.text.split(' ')
        command_name = command_split[0]
        command_args = tools.qlist(command_split[1:], except_val='')
        try:
            command = commands.get_command(command_name)
        except KeyError:
            self.invalid_input()
        else:
            print_result = command.do(self.game_instance, command_args)
            if print_result is not None:
                self.output(print_result, end='\n')
        finally:
            self.reset()

    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.output(strings.Debug.INVALID_INPUT, end='\n')
