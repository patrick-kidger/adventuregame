import sys

import Tools as tools

import Maze.config.config as config
import Maze.config.strings as strings
import Maze.lib.getch as getch


class BaseIO(object):
    def __init__(self):
        self.interface = None
        super(BaseIO, self).__init__()
        
    def register_interface(self, interface):
        """Lets the BaseIO instance know what interface it is used with."""
        self.interface = interface


class Output(BaseIO):
    """Handles outputting to the screen."""
    
    default_output_kwargs = {'end': ""}
    
    def __init__(self, opts=None):
        if opts is None:
            opts = {}
        self.default_opts = {}
        self.default_opts.update(self.default_output_kwargs)
        self.default_opts.update(opts)
        self.opts = self.default_opts
        super(Output, self).__init__()
    
    def __call__(self, outputstr, width=None, flush=True, **kwargs):
        updated_opts = dict(self.opts, **kwargs)
        if width is not None:
            outputstr = '{{:{}}}'.format(width).format(outputstr)
        print(outputstr, **updated_opts)
        if flush:
            sys.stdout.flush()
            
    def context(self, opts=None, **kwargs):
        """Changes the current options to the default options updated with the arguments passed."""
        if opts is None:
            opts = {}
        self.opts = dict(self.default_opts, **opts)
        self.opts.update(**kwargs)

    @staticmethod
    def flush():
        """Flushes stdout."""
        sys.stdout.flush()
        
    def sep(self, length, **kwargs):
        """Prints a separator of the given length."""
        self(strings.Sep.sep * length, **kwargs)
        
    def no_flush_context(self):
        """Provides an easy wrapper for the common context of wanting to print a lot
        of lines and only flush at the end."""
        class NoFlushClass(object):
            def __enter__(*args, **kwargs):
                self.context(flush=False)

            def __exit__(*args, **kwargs):
                self.context()
                self.flush()
        return NoFlushClass()
        
    def table(self, header, columns, edge_space=''):
        column_widths = []
        # In case we're passed generators that get consumed
        columns = [list(column) for column in columns]
        for column in columns:
            column_width = 0
            for column_entry in column:
                column_width = max(column_width, len(column_entry))
            column_widths.append(column_width)
        overall_header_width = len(header) + len(edge_space) * 2                      # The width of the header text, plus space to either side of it
        overall_column_width = (sum(column_widths) +                                  # The width of the columns
                                len(column_widths) * len(edge_space) * 2 +            # The width of the space either side of the entry in each column
                                (len(column_widths) - 1) * len(strings.Sep.vert_sep)) # The width of the lines separating columns
        overall_width = max(overall_header_width, overall_column_width)
        if overall_header_width > overall_column_width:
            column_widths[-1] += overall_header_width - overall_column_width
                           
        rows = zip(*columns)
        
        with self.no_flush_context():
            self(strings.Sep.dr_sep)
            self.sep(overall_width)
            self(strings.Sep.dl_sep, end='\n')
            self(strings.Sep.ud_sep)
            self(edge_space + header + edge_space, width=overall_width)
            self(strings.Sep.ud_sep, end='\n')
            self(strings.Sep.udr_sep)
            self.sep(overall_width)
            self(strings.Sep.udl_sep, end='\n')
            for row in rows:
                self(strings.Sep.ud_sep)
                for i, entry in enumerate(row):
                    self(edge_space)
                    self(entry, width=column_widths[i])
                    self(edge_space)
                    self(strings.Sep.ud_sep)
                self('\n')
            self(strings.Sep.ur_sep)
            self.sep(overall_width)
            self(strings.Sep.ul_sep, end='\n')


class BaseInput(BaseIO, tools.dynamic_subclassing_by_attr('input_name')):
    """Handles receiving user input."""
    def __call__(self, inputstr, type_arg=lambda x: x, num_chars=1, end=''):
        if num_chars == -1:
            input_ = input(inputstr)
        else:
            self.interface.output(inputstr)
            input_ = ''
            for _ in range(num_chars):
                input_ += self.get_char()
            self.interface.output('', end=end)
        return type_arg(input_)
        
    def get_char(self, print_char=True):
        """Gets a single character from the terminal."""
        while True:
            raw_input = getch.getch()
            if raw_input == b'\x03':
                raise KeyboardInterrupt
                
            try:
                input_ = str(raw_input, 'utf-8')
            except UnicodeDecodeError:
                pass
            else:
                break
                
        if print_char:
            self.interface.output(input_)
        return input_
        
    def set(self, subclass_name):
        """Turns the instance into one of its registered subclasses."""
        self.pick_subclass(subclass_name)
        
    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.interface.output(config.INVALID_INPUT, end='\n')
        

class SelectMapInput(BaseInput):
    input_name = config.InputInterfaces.SELECTMAP


class PlayInput(BaseInput):
    """Handles the inputs for the main playing of the game."""
    input_name = config.InputInterfaces.PLAY

    def move_inp(self, inputstr):
        inp_dict = {config.Move.UP: config.Play.UP,
                    config.Move.DOWN: config.Play.DOWN,
                    config.Move.VERTICAL_UP: config.Play.VERTICAL_UP,
                    config.Move.VERTICAL_DOWN: config.Play.VERTICAL_DOWN,
                    config.Move.LEFT: config.Play.LEFT,
                    config.Move.RIGHT: config.Play.RIGHT}
        while True:
            inp = self(inputstr).lower()
            if inp == config.Input.ESCAPE:
                inp = self('', num_chars=-1)
            else:
                self.interface.output('\n')
                
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
