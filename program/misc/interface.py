import math

import Tools as tools

import Maze.config.config as config
import Maze.config.strings as strings
import Maze.program.misc.helpers as helpers
import Maze.program.misc.inputs as inputs
import Maze.program.misc.sdl as sdl


class BaseIO(object):
    def __init__(self):
        self.interface = None
        super(BaseIO, self).__init__()
        
    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.interface = interface


class BaseOverlay(BaseIO):
    default_output_kwargs = {}

    def __init__(self, name, location, size, background_color, enabled):
        self.name = name
        self.location = location
        self.screen = sdl.Surface(size)
        self.background_color = background_color
        self.enabled = enabled

        self.output = None
        super(BaseIO, self).__init__()

    def __call__(self, output_val, flush=False):
        # Just a convenience, to allow for just calling with flush=True as an argument, rather than putting an
        # output.flush() on the next line.
        if flush:
            self.output.flush(self.name)

    def register_output(self, output):
        """Lets the BaseOverlay instance know what output it is used with."""
        self.output = output

    def toggle(self):
        """Toggles whether or not this overlay is enabled."""
        self.enabled = not self.enabled

    def clear(self, flush=False):
        """Clears the overlay of everything that has been printed to it."""
        self.wipe(flush)

    def wipe(self, flush=False):
        """Fills the overlay with its background color."""
        self.screen.fill(self.background_color)
        if flush:
            self.output.flush(self.name)


class GraphicsOverlay(BaseOverlay):
    """Handles outputting graphics to the screen."""


class TextOverlay(BaseOverlay):
    """Handles outputting text to the screen."""
    
    def __init__(self, *args, **kwargs):
        self.font = sdl.ftfont.SysFont(config.FONT_NAME, config.FONT_SIZE)
        self.text = ''
        super(TextOverlay, self).__init__(*args, **kwargs)

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
            text = self.font.render(output_text, False, config.FONT_COLOR)
            text_area = self.screen.blit(text, text_cursor)
            text_cursor = (0, text_area.bottom)
        super(TextOverlay, self).__call__(output_val, **kwargs)

    def clear(self, flush=False):
        super(TextOverlay, self).clear(flush)
        self.text = ''

    def sep(self, length, **kwargs):
        """Prints a separator of the given length."""
        self(strings.Sep.sep * length, **kwargs)

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
        overall_title_width = len(title) + len(edge_space) * 2                        # The width of the header text, plus space to either side of it
        overall_column_width = (sum(column_widths) +                                  # The width of the columns
                                len(column_widths) * len(edge_space) * 2 +            # The width of the space either side of the entry in each column
                                (len(column_widths) - 1) * len(strings.Sep.vert_sep)) # The width of the lines separating columns
        overall_width = max(overall_title_width, overall_column_width)
        if overall_title_width > overall_column_width:
            column_widths[-1] += overall_title_width - overall_column_width
                           
        rows = zip(*columns)

        self(strings.Sep.dr_sep)
        self.sep(overall_width)
        self(strings.Sep.dl_sep, end='\n')
        self(strings.Sep.ud_sep)
        self(edge_space + title + edge_space, width=overall_width)
        self(strings.Sep.ud_sep, end='\n')
        self(strings.Sep.udr_sep)
        self.sep(overall_width)
        self(strings.Sep.udl_sep, end='\n')
        if headers is not None:
            self(strings.Sep.ud_sep)
            for header, column_width in zip(headers, column_widths):
                self(edge_space)
                self(header, width=column_width)
                self(edge_space)
                self(strings.Sep.ud_sep)
            self('\n')
            self(strings.Sep.ud_sep)
            for column_width in column_widths[:-1]:
                self.sep(column_width)
                self(strings.Sep.udlr_sep)
            self.sep(column_widths[-1])
            self(strings.Sep.ud_sep, end='\n')
        for row in rows:
            self(strings.Sep.ud_sep)
            for entry, column_width in zip(row, column_widths):
                self(edge_space)
                self(entry, width=column_width)
                self(edge_space)
                self(strings.Sep.ud_sep)
            self('\n')
        self(strings.Sep.ur_sep)
        self.sep(overall_width)
        self(strings.Sep.ul_sep, end='\n')


class Output(BaseIO):
    """The overall output. It takes its various overlays and then combines them to produce output to the screen."""
    def __init__(self, overlays):
        self.overlays = overlays
        self.overlays.debug.register_output(self)
        self.overlays.game.register_output(self)

        self.screen = sdl.display.set_mode(config.SCREEN_SIZE)
        sdl.display.set_caption(config.WINDOW_NAME)
        super(Output, self).__init__()

    def flush(self, overlay_names=None):
        """Pushes the changes from the overlays to the main screen.

        :str or tuple overlay_names: The names of the overlays to update."""
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


class Input(BaseIO):
    """Handles receiving user input."""
    def debug_inp(self, num_chars=math.inf, type_arg=lambda x: x):
        """Input into the debug console"""
        debug_console_enabled = self.interface.output.overlays.debug.enabled
        self.interface.output.overlays.debug.enabled = True
        input_ = helpers.input_(num_chars=num_chars,
                                output=self.interface.output.overlays.debug,
                                flush=self.interface.output.flush,
                                done=(sdl.K_KP_ENTER, sdl.K_RETURN, sdl.K_ESCAPE, sdl.K_BACKSLASH))
        self.interface.output.overlays.debug.enabled = debug_console_enabled
        return type_arg(input_)

    def debug_command(self, command):
        """Finds the debug command corresponding to the string inputted. Returns either the command (as a function,
        needing a maze game instance to be passed to it), or None, if it could not find a corresponding command."""
        command_split = command.split(' ')
        command_name = command_split[0]
        if command_name in config.DebugInput:
            command_args = tools.qlist(command_split[1:], except_val='')
            special_input = inputs.SpecialInput.find_subclass(command_name)
            return lambda maze_game: special_input.do(maze_game, command_args)
        else:
            self.invalid_input()
            return None

    def play_inp(self):
        """The usual input for playing the game."""
        move_commands = {config.Move.UP: config.Play.UP,
                         config.Move.DOWN: config.Play.DOWN,
                         config.Move.VERTICAL_UP: config.Play.VERTICAL_UP,
                         config.Move.VERTICAL_DOWN: config.Play.VERTICAL_DOWN,
                         config.Move.LEFT: config.Play.LEFT,
                         config.Move.RIGHT: config.Play.RIGHT}
        while True:
            inp = helpers.input_(num_chars=1).lower()
            if inp == config.OPEN_CONSOLE:
                self.interface.output.overlays.debug.enabled = not self.interface.output.overlays.debug.enabled
                self.interface.output.flush()

            if (inp == config.OPEN_CONSOLE or inp == config.SELECT_CONSOLE) and self.interface.output.overlays.debug.enabled:
                debug_inp = self.debug_inp()
                debug_com = self.debug_command(debug_inp)
                if debug_com is not None:
                    return debug_com, False

            if inp in move_commands:
                return move_commands[inp], True

    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.interface.output.overlays.debug(strings.Play.INVALID_INPUT, end='\n')
        self.interface.output.flush('debug')

        
class Interface(object):
    """Wrapper around Output and Input, in order to provide the overall interface."""
    def __init__(self, input_, output):
        self.input = input_
        self.output = output
        self.input.register_interface(self)
        self.output.register_interface(self)
