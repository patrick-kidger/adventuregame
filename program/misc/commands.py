import Tools as tools


import Game.config.config as config
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class CommandRunner:
    def __init__(self, game_objects, interface):
        self.game_objects = game_objects
        self.interface = interface
        self.debug_mode = False

    def run_command(self, command_name, command_args):
        try:
            command = SpecialInput.find_subclass(command_name)
        except KeyError:
            return strings.Debug.INVALID_INPUT
        else:
            if self.debug_mode or not command.needs_debug:
                return command.do(command_args, self)
            else:
                return strings.Debug.DEBUG_NOT_ENABLED


class SpecialInput(tools.SubclassTrackerMixin('inp')):
    """Base class for special inputs."""
    inp = ''             # What string should inputted to get this input
    needs_debug = False  # Whether this input needs debug mode enabled to work

    @tools.classproperty
    def description(cls):
        """Default description for a special input is its docstring."""
        return cls.__doc__
    
    @classmethod
    def do(cls, inp_args, command_runner):
        """This is the function that should be called to invoke a special action."""
        # Does not raise NotImplementedError as this is called when running an empty command.


class Variable(SpecialInput):
    """Provides a simple base class for setting variables."""
    variables = tuple()   # The name of the variables to set
    variable_type = bool  # The type of the variable that this command sets
    
    @classmethod
    def do(cls, inp_args, command_runner):
        variable_value_to_set = inp_args[0]
        for variable_name in cls.variables:
            current_variable_value = tools.deepgetattr(command_runner, variable_name)
            if cls.variable_type is bool:
                variable_value = cls.toggle(variable_value_to_set, current_variable_value)
            else:
                try:
                    variable_value = cls.variable_type(variable_value_to_set)
                except ValueError:
                    return strings.Debug.VARIABLE_SET_FAILED.format(value=variable_value_to_set,
                                                                    variable_type=cls.variable_type)
            tools.deepsetattr(command_runner, variable_name, variable_value)
            command_runner.interface.out('debug', strings.Debug.VARIABLE_SET.format(variable=variable_name,
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
    def do(cls, inp_args, command_runner):
        command_searched_for = inp_args[0]
        
        def output_matched_commands(command_dict, table_header):
            commands_matched = [x for x in command_dict.keys() if command_searched_for in x]
            if commands_matched:
                commands_matched_values = (command_dict[x] for x in commands_matched)
                command_help_strings = [x.description for x in commands_matched_values]
                command_runner.interface.overlays.debug.table(title=table_header,
                                                              columns=[commands_matched, command_help_strings])
                
        output_matched_commands(Help.commands, strings.Debug.HEADER)
        if command_runner.debug_mode:
            output_matched_commands(Debug.commands, strings.Debug.DEBUG_HEADER)


# Register help with itself. Can't do this via decorator as Help hasn't yet been defined at decoration time.
Help.commands[config.DebugCommands.HELP] = Help


@tools.register(config.DebugCommands.CLEAR, Help.commands)
class Clear(SpecialInput):
    """Clears the debug console of text."""
    inp = config.DebugCommands.CLEAR

    @classmethod
    def do(cls, inp_args, command_runner):
        command_runner.interface.overlays.debug.reset(prompt=False)


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
    variables = ('game_objects.player.incorporeal', 'game_objects.player.flight')
    needs_debug = True
    
 
@tools.register(config.DebugCommands.FLY, Debug.commands)
class Fly(Variable):
    """Sets whether the player can fly or not."""
    inp = config.DebugCommands.FLY
    variables = ('game_objects.player.flight',)
    needs_debug = True


@tools.register(config.DebugCommands.GHOST, Debug.commands)
class Ghost(Variable):
    """Sets whether the player is incorporeal or not."""
    inp = config.DebugCommands.GHOST
    variables = ('game_objects.player.incorporeal',)
    needs_debug = True


@tools.register(config.DebugCommands.SETSPEED, Debug.commands)
class SetSpeed(Variable):
    """Sets the player's speed."""
    inp = config.DebugCommands.SETSPEED
    variables = ('game_objects.player.speedmult',)
    variable_type = float
    needs_debug = True


@tools.register(config.DebugCommands.CLOSE, Help.commands)
class Close(SpecialInput):
    """Closes the whole game."""
    inp = config.DebugCommands.CLOSE

    @classmethod
    def do(cls, inp_args, command_runner):
        raise exceptions.CloseException()


@tools.register(config.DebugCommands.QUIT, Help.commands)
class Quit(SpecialInput):
    """Quits the game back to the main screen."""
    inp = config.DebugCommands.QUIT

    @classmethod
    def do(cls, inp_args, command_runner):
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
    def do(cls, inp_args, command_runner):
        if command_runner.game_objects.map.initialised:
            player = command_runner.game_objects.player
            tile = command_runner.game_objects.map.get(player.tile_x, player.tile_y, player.z)

            variable_name = inp_args[0]
            if variable_name == '':
                return str(tile)
            else:
                try:
                    return str(tools.deepgetattr(tile, variable_name))
                except (AttributeError, sdl.error):
                    return strings.Debug.VARIABLE_GET_FAILED.format(variable=variable_name)
        else:
            return strings.Debug.GAME_NOT_STARTED


@tools.register(config.DebugCommands.GET, Debug.commands)
class Get(SpecialInput):
    """Gets the value of a variable."""
    inp = config.DebugCommands.GET
    needs_debug = True
    
    @classmethod
    def do(cls, inp_args, command_runner):
        variable_name = inp_args[0]
        try:
            variable_value = tools.deepgetattr(command_runner, variable_name)
        except (AttributeError, sdl.error):
            return strings.Debug.VARIABLE_GET_FAILED.format(variable=variable_name)
        else:
            return strings.Debug.VARIABLE_GET.format(variable=variable_name, value=repr(variable_value))
