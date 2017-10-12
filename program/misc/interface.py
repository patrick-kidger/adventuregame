import copy
import math
import re
import pygame.ftfont
import pygame.display
import pygame.event

import Tools as tools

import Maze.config.config as config
import Maze.config.strings as strings
import Maze.program.misc.helpers as helpers


pygame.ftfont.init()
pygame.display.init()


class BaseIO(object):
    def __init__(self):
        self.interface = None
        super(BaseIO, self).__init__()
        
    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.interface = interface


class BaseOverlay(BaseIO):
    default_output_kwargs = {}

    def __init__(self, location, size, opts=None):
        if opts is None:
            opts = {}
        self.default_opts = {}
        self.default_opts.update(self.default_output_kwargs)
        self.default_opts.update(opts)
        self.opts = copy.deepcopy(self.default_opts)

        self.location = location
        self.screen = pygame.Surface(size)

        self.output = None
        super(BaseIO, self).__init__()

    def register_output(self, output):
        """Lets the BaseOverlay instance know what output it is used with."""
        self.output = output

    def context(self, opts=None, **kwargs):
        """Changes the current options to the default options updated with the arguments passed."""
        if opts is None:
            opts = {}
        self.opts = dict(self.default_opts, **opts)
        self.opts.update(**kwargs)

    def no_flush_context(self):
        """Provides an easy wrapper for the common context of wanting to output a lot without flushing, and then flush
        at the end."""
        class NoFlushClass(object):
            def __enter__(no_flush):
                no_flush.old_opts = copy.deepcopy(self.opts)
                self.context(no_flush.old_opts, flush=False)

            def __exit__(no_flush, *args, **kwargs):
                self.context(no_flush.old_opts)
                if no_flush.old_opts['flush']:
                    self.flush()
        return NoFlushClass()

    def flush(self):
        """Updates the display."""
        updated_area = self.output.screen.blit(self.screen, self.location)
        pygame.display.update(updated_area)


class GraphicsOverlay(BaseOverlay):
    pass


class TextOverlay(BaseOverlay):
    """Handles outputting to the screen."""
    
    default_output_kwargs = {'end': "", 'flush': True}
    
    def __init__(self, *args, **kwargs):
        self.font = pygame.ftfont.SysFont(config.FONT_NAME, config.FONT_SIZE)
        self.text = ''
        super(TextOverlay, self).__init__(*args, **kwargs)

    def __call__(self, outputstr, width=None, **kwargs):
        """Outputs text.

        :str outputstr: The string to output.
        :int width: Optional. The text with be padded to this width."""

        updated_opts = dict(self.opts, **kwargs)

        outputstr += updated_opts['end']
        if width is not None:
            outputstr = '{{:{}}}'.format(width).format(outputstr)
        self.text += outputstr
        # \x08 = backspace. \b doesn't work for some reason.
        self.text = helpers.re_sub_recursive(r'[^\x08]\x08', '', self.text)
        self.text.lstrip('\b')

        self.screen.fill(config.SCREEN_BACKGROUND_COLOR)

        split_text = self.text.split('\n')
        text_cursor = (0, 0)
        for output_text in split_text:
            text = self.font.render(output_text, False, config.FONT_COLOR)
            text_area = self.screen.blit(text, text_cursor)
            text_cursor = (0, text_area.bottom)

        if updated_opts['flush']:
            self.flush()

    def clear(self, **kwargs):
        updated_opts = dict(self.opts, **kwargs)
        self.screen.fill(config.SCREEN_BACKGROUND_COLOR)
        if updated_opts['flush']:
            pygame.display.flip()
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
        
        with self.no_flush_context():
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
    def __init__(self, debug, game):
        self.debug = debug
        self.game = game
        self.debug.register_output(self)
        self.game.register_output(self)

        self.screen = pygame.display.set_mode(config.SCREEN_SIZE)
        pygame.display.set_caption(config.WINDOW_NAME)
        super(Output, self).__init__()


class BaseInput(BaseIO, tools.dynamic_subclassing_by_attr('input_name')):
    """Handles receiving user input."""
    def __call__(self, inputstr='', num_chars=1, end='', print_received_input=False, type_arg=lambda x: x):
        self.interface.output.debug(inputstr)
        if print_received_input:
            input_ = helpers.input_pygame(num_chars, self.interface.output.debug, flush=True)
        else:
            input_ = helpers.input_pygame(num_chars)
        self.interface.output.debug(end)
        return type_arg(input_)
        
    def set(self, subclass_name):
        """Turns the instance into one of its registered subclasses."""
        self.pick_subclass(subclass_name)
        
    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.interface.output.debug(strings.Play.INVALID_INPUT, end='\n')
        

class SelectMapInput(BaseInput):
    input_name = config.InputInterfaces.SELECTMAP


class PlayInput(BaseInput):
    """Handles the inputs for the main playing of the game."""
    input_name = config.InputInterfaces.PLAY

    def play_inp(self):
        """The usual input for playing the game."""
        inp_dict = {config.Move.UP: config.Play.UP,
                    config.Move.DOWN: config.Play.DOWN,
                    config.Move.VERTICAL_UP: config.Play.VERTICAL_UP,
                    config.Move.VERTICAL_DOWN: config.Play.VERTICAL_DOWN,
                    config.Move.LEFT: config.Play.LEFT,
                    config.Move.RIGHT: config.Play.RIGHT}
        while True:
            inp = self().lower()
            if inp == config.Input.ESCAPE:
                self.interface.output.debug(config.Input.ESCAPE)
                inp = self('', num_chars=math.inf, print_received_input=True)
                
            if inp.split(' ')[0] in config.Input:
                try:
                    returnstr = inp_dict[inp]
                except KeyError:
                    returnstr = inp
                is_move = inp in config.Move
                return returnstr, is_move
            else:
                self.invalid_input()
            
        
class Interface(object):
    """Wrapper around Output and Input, in order to provide the overall interface."""
    def __init__(self, input_, output):
        self.input = input_
        self.output = output
        self.input.register_interface(self)
        self.output.register_interface(self)
