import math
import Tools as tools


import Game.config.config as config
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl

import Game.program.tiles as tiles


def get_command(command_name):
    return SpecialInput.find_subclass(command_name)


class SpecialInput(tools.SubclassTrackerMixin('inp')):
    """Base class for special inputs."""
    inp = ''             # What string should inputted to get this input
    needs_debug = False  # Whether this input needs debug mode enabled to work

    # Evil hackery to make debug commands only work when in debug mode.
    def __init_subclass__(cls, **kwargs):
        super(SpecialInput, cls).__init_subclass__(**kwargs)

        # If this command needs debug mode enabled...
        if cls.needs_debug:
            old_do = cls.do

            # ... then wrap the command in a function to check if debug is enabled
            def do(cls_, game_instance, inp_args):
                if game_instance.debug_mode:
                    # __func__ to get the original (not bound) method
                    return old_do.__func__(cls_, game_instance, inp_args)
                else:
                    game_instance.interface.out('debug', strings.Debug.DEBUG_NOT_ENABLED, end='\n')

            cls.do = classmethod(do)

    @tools.classproperty
    def description(cls):
        """Default description for a special input is its docstring."""
        return cls.__doc__
    
    @classmethod
    def do(cls, game_instance, inp_args):
        """This is the function that should be called to invoke a special action."""
    
        
class Variable(SpecialInput):
    """Provides a simple base class for setting variables."""
    variables = tuple()   # The name of the variables to set
    variable_type = bool  # The type of the variable that this command sets
    
    @classmethod
    def do(cls, game_instance, inp_args):
        variable_value_to_set = inp_args[0]
        for variable_name in cls.variables:
            current_variable_value = tools.deepgetattr(game_instance, variable_name)
            if cls.variable_type is bool:
                variable_value = cls.toggle(variable_value_to_set, current_variable_value)
            else:
                try:
                    variable_value = cls.variable_type(variable_value_to_set)
                except ValueError:
                    return strings.Debug.VARIABLE_SET_FAILED.format(value=variable_value_to_set,
                                                                    variable_type=cls.variable_type)
            tools.deepsetattr(game_instance, variable_name, variable_value)
            game_instance.interface.out('debug', strings.Debug.VARIABLE_SET.format(variable=variable_name,
                                                                                   value=variable_value),
                                        end='\n')
        
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
    def do(cls, game_instance, inp_args):
        command_searched_for = inp_args[0]
        
        def output_matched_commands(command_dict, table_header):
            commands_matched = [x for x in command_dict.keys() if command_searched_for in x]
            if commands_matched:
                commands_matched_values = (command_dict[x] for x in commands_matched)
                command_help_strings = [x.description for x in commands_matched_values]
                game_instance.interface.overlays.debug.table(title=table_header, columns=[commands_matched, command_help_strings])
                
        output_matched_commands(Help.commands, strings.Debug.HEADER)
        if game_instance.debug_mode:
            output_matched_commands(Debug.commands, strings.Debug.DEBUG_HEADER)


# Register help with itself. Can't do this via decorator as Help hasn't yet been defined at decoration time.
Help.commands[config.DebugCommands.HELP] = Help


@tools.register(config.DebugCommands.CLEAR, Help.commands)
class Clear(SpecialInput):
    """Clears the debug console of text."""
    inp = config.DebugCommands.CLEAR

    @classmethod
    def do(cls, game_instance, inp_args):
        game_instance.interface.overlays.debug.reset(prompt=False)


@tools.register(config.DebugCommands.DEBUG, Help.commands)
class Debug(Variable):
    """Sets the debug state."""
    inp = config.DebugCommands.DEBUG
    variables = ('debug_mode',)
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


@tools.register(config.DebugCommands.SETSPEED, Debug.commands)
class SetSpeed(Variable):
    """Sets the player's speed."""
    inp = config.DebugCommands.SETSPEED
    variables = ('player.speedmult',)
    variable_type = float
    needs_debug = True


@tools.register(config.DebugCommands.CLOSE, Help.commands)
class Close(SpecialInput):
    """Closes the whole game."""
    inp = config.DebugCommands.CLOSE

    @classmethod
    def do(cls, game_instance, inp_args):
        raise exceptions.CloseException()


@tools.register(config.DebugCommands.QUIT, Help.commands)
class Quit(SpecialInput):
    """Quits the game back to the main screen."""
    inp = config.DebugCommands.QUIT

    @classmethod
    def do(cls, game_instance, inp_args):
        raise exceptions.QuitException()


@tools.register(config.DebugCommands.EXIT, Help.commands)
class Exit(Quit):
    """Quits the game back to the main screen."""
    inp = config.DebugCommands.EXIT


@tools.register(config.DebugCommands.CURRENT_TILE, Debug.commands)
class CurrentTile(SpecialInput):
    """Gets an attribute of the tile that the player is currently over. If an attribute argument is not passed then the
    tile itself is printed."""
    inp = config.DebugCommands.CURRENT_TILE
    needs_debug = True
    description = "Get an attribute of the tile that the player is currently over."

    @classmethod
    def do(cls, game_instance, inp_args):
        tile_x = math.floor(game_instance.player.x / tiles.size)
        tile_y = math.floor(game_instance.player.y / tiles.size)
        tile = game_instance.map[tools.Object(x=tile_x, y=tile_y, z=game_instance.player.z)]

        variable_name = inp_args[0]
        if variable_name == '':
            return str(tile)
        else:
            try:
                return str(tools.deepgetattr(tile, variable_name))
            except (AttributeError, sdl.error):
                return strings.Debug.VARIABLE_GET_FAILED.format(variable=variable_name)


@tools.register(config.DebugCommands.GET, Debug.commands)
class Get(SpecialInput):
    """Gets the value of a variable."""
    inp = config.DebugCommands.GET
    needs_debug = True
    
    @classmethod
    def do(cls, game_instance, inp_args):
        variable_name = inp_args[0]
        try:
            variable_value = tools.deepgetattr(game_instance, variable_name)
        except (AttributeError, sdl.error):
            return strings.Debug.VARIABLE_GET_FAILED.format(variable=variable_name)
        else:
            return strings.Debug.VARIABLE_GET.format(variable=variable_name, value=repr(variable_value))
