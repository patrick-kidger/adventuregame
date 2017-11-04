import Tools as tools


import config.config as config
import config.strings as strings

import program.misc.exceptions as exceptions


def get_command(command_name):
    return SpecialInput.find_subclass(command_name)


SpecialInputSubclassTracker = tools.subclass_tracker('inp')

# Evil metaclass hackery, primarily to make debug commands only work when in debug mode.
# tools.subclass_tracker works via metaclass, so we have to inherit it here.
class SpecialInputMetaclass(SpecialInputSubclassTracker.__class__):
    def __getattribute__(cls, item):
        # If this command needs debug mode enabled...
        if item == 'do' and cls.needs_debug:
            do = super(SpecialInputMetaclass, cls).__getattribute__(item)
            # ... then wrap the command in a function to check if debug is enabled
            def do_debug_wrapper(maze_game, inp_args):
                if maze_game.debug:
                    # Does not need 'cls' passed as an argument as it is already a bound method.
                    returnval = do(maze_game, inp_args)
                else:
                    maze_game.out.overlays.debug(strings.Play.DEBUG_NOT_ENABLED, end='\n', flush=True)
                    returnval = SpecialInput  # No special return value, as the input wasn't executed.
                return returnval
            return do_debug_wrapper
            
        else:
            return super(SpecialInputMetaclass, cls).__getattribute__(item)
    
    # There is no classmethod-property decorator, so we just put this on the metaclass.
    @property
    def description(cls):
        """Default description for a special input is its docstring."""
        return cls.__doc__


class SpecialInput(SpecialInputSubclassTracker, metaclass=SpecialInputMetaclass):
    """Base class for special inputs."""
    inp = ''             # What string should inputted to get this input
    needs_debug = False  # Whether this input needs debug mode enabled to work
    
    @classmethod
    def do(cls, maze_game, inp_args):
        """This is the function that should be called to invoke a special action."""
    
        
class Variable(SpecialInput):
    """Provides a simple base class for setting variables."""
    variables = tuple()   # The name of the variables to set
    variable_bool = True  # If the variables are boolean
    
    @classmethod
    def do(cls, maze_game, inp_args):
        variable_value_to_set = inp_args[0]
        for variable_name in cls.variables:
            current_variable_value = tools.deepgetattr(maze_game, variable_name)
            if cls.variable_bool:
                variable_value = cls.toggle(variable_value_to_set, current_variable_value)
            else:
                variable_value = variable_value_to_set
            tools.deepsetattr(maze_game, variable_name, variable_value)
            maze_game.out.overlays.debug(strings.Play.VARIABLE_SET.format(variable=variable_name, value=variable_value),
                                         end='\n', flush=True)
        
    @staticmethod
    def bool_(inp):
        return inp.lower() in ['true', '1']

    @classmethod
    def toggle(cls, inp, val):
        if inp == '':
            return not val
        else:
            return cls.bool_(inp)


class Help(SpecialInput):
    """Displays the available commands."""
    inp = config.DebugCommands.HELP
    commands = tools.SortedDict()
    description = "Displays this help menu."
    
    @classmethod
    def do(cls, maze_game, inp_args):
        command_searched_for = inp_args[0]
        
        def output_matched_commands(command_dict, table_header):
            commands_matched = [x for x in command_dict.keys() if command_searched_for in x]
            if commands_matched:
                commands_matched_values = (command_dict[x] for x in commands_matched)
                command_help_strings = [x.description for x in commands_matched_values]
                maze_game.out.overlays.debug.table(title=table_header, columns=[commands_matched, command_help_strings])
                
        output_matched_commands(Help.commands, strings.Help.HEADER)
        if maze_game.debug:
            output_matched_commands(Debug.commands, strings.Help.DEBUG_HEADER)
        maze_game.out.flush()


# Register help with itself. Can't do this via decorator as Help hasn't yet been defined at decoration time.
Help.commands[config.DebugCommands.HELP] = Help


@tools.register(config.DebugCommands.CLEAR, Help.commands)
class Clear(SpecialInput):
    """Clears the debug console of text."""
    inp = config.DebugCommands.CLEAR

    @classmethod
    def do(cls, maze_game, inp_args):
        maze_game.out.overlays.debug.reset(flush=True)


@tools.register(config.DebugCommands.DEBUG, Help.commands)
class Debug(Variable):
    """Sets the debug state."""
    inp = config.DebugCommands.DEBUG
    variables = ('debug',)
    commands = tools.SortedDict()


@tools.register(config.DebugCommands.NOCLIP, Debug.commands)
class NoClip(Variable):
    """Sets whether the player is incorporeal and can fly or not."""
    inp = config.DebugCommands.NOCLIP
    variables = ('player.incorporeal', 'player.flight')
    needs_debug = True
    
 
@tools.register(config.DebugCommands.FLY, Debug.commands)
class Fly(Variable):
    """Sets whether the player can fly or not."""
    inp = config.DebugCommands.FLY
    variables = ('player.flight',)
    needs_debug = True


@tools.register(config.DebugCommands.GHOST, Debug.commands)
class Ghost(Variable):
    """Sets whether the player is incorporeal or not."""
    inp = config.DebugCommands.GHOST
    variables = ('player.incorporeal',)
    needs_debug = True

    
@tools.register(config.DebugCommands.CHANGEMAP, Debug.commands)
class ChangeMap(SpecialInput):
    """Changes the map."""
    inp = config.DebugCommands.CHANGEMAP
    needs_debug = True
    
    @classmethod
    def do(cls, maze_game, inp_args):
        raise exceptions.MapSelectException()


@tools.register(config.DebugCommands.CLOSE, Help.commands)
class Close(SpecialInput):
    """Closes the whole game."""
    inp = config.DebugCommands.CLOSE

    @classmethod
    def do(cls, maze_game, inp_args):
        raise exceptions.CloseException()


@tools.register(config.DebugCommands.QUIT, Help.commands)
class Quit(SpecialInput):
    """Quits the game back to the main screen."""
    inp = config.DebugCommands.QUIT

    @classmethod
    def do(cls, maze_game, inp_args):
        raise exceptions.QuitException()


@tools.register(config.DebugCommands.EXIT, Help.commands)
class Exit(Quit):
    """Quits the game back to the main screen."""
    inp = config.DebugCommands.EXIT


@tools.register(config.DebugCommands.RESET, Debug.commands)
class Reset(SpecialInput):
    """Resets the game."""
    inp = config.DebugCommands.RESET
    needs_debug = True

    @classmethod
    def do(cls, maze_game, inp_args):
        raise exceptions.ResetException()


@tools.register(config.DebugCommands.GET, Debug.commands)
class Get(SpecialInput):
    """Gets the value of a variable."""
    inp = config.DebugCommands.GET
    needs_debug = True
    
    @classmethod
    def do(cls, maze_game, inp_args):
        variable_name = inp_args[0]
        try:
            variable_value = tools.deepgetattr(maze_game, variable_name)
        except AttributeError:
            maze_game.out.overlays.debug(strings.Play.VARIABLE_GET_FAILED.format(variable=variable_name), end='\n',
                                         flush=True)
        else:
            maze_game.out.overlays.debug(strings.Play.VARIABLE_GET.format(variable=variable_name, value=variable_value),
                                         end='\n', flush=True)
