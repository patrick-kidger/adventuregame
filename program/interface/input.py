import math
import Tools as tools


import config.config as config
import config.internal_strings as internal_strings
import config.strings as strings

import program.interface.base as base

import program.misc.exceptions as exceptions
import program.misc.commands as commands
import program.misc.sdl as sdl


class BaseListener(base.BaseIO):
    """An abstract base class for listeners."""

    def __init__(self, name):
        self.name = name
        super(BaseListener, self).__init__()


class PlayListener(BaseListener):
    def __call__(self):
        char, key_code = sdl.text_stream(single_event=True, discard_old=True)

        if char in config.Move:
            return config.Move.Direction[char], internal_strings.InputTypes.MOVEMENT

        if char == config.OPEN_CONSOLE:
            self.out.overlays.debug.toggle()
            self.out.flush()

        if char in (config.OPEN_CONSOLE, config.SELECT_CONSOLE) and self.out.overlays.debug.enabled:
            self.inp.add_listener(internal_strings.ListenerNames.DEBUG)

        return None, internal_strings.InputTypes.NO_INPUT


class TextListener(BaseListener):
    def __init__(self, overlay, name):
        self.overlay = overlay
        super(TextListener, self).__init__(name)


class DebugListener(TextListener):
    def __init__(self, overlay, name):
        self.text = ''
        super(DebugListener, self).__init__(overlay, name)

    def __call__(self, num_chars=math.inf, command=True, wait=False):
        return_lambda = None
        first_pass = True
        while wait or first_pass:
            first_pass = False
            self.text, char, key_code = sdl.modify_text(self.text,
                                                        char_done=(config.OPEN_CONSOLE, config.SELECT_CONSOLE),
                                                        output=self.overlay,
                                                        flush=self.overlay.flush)

            if key_code in sdl.K_ENTER or len(self.text) >= num_chars:
                self.overlay('\n')
                self.overlay.flush()
                self.text = self.text[:num_chars if num_chars != math.inf else None]  # Infinity not supported in slices
                return_lambda = self.debug_command(self.text) if command else self.text
                self.text = ''
                wait = False
            if key_code == sdl.K_ESCAPE or char == config.OPEN_CONSOLE:
                self.overlay.enabled = False
            if key_code == sdl.K_ESCAPE or char in (config.OPEN_CONSOLE, config.SELECT_CONSOLE):
                self.inp.remove_listener(internal_strings.ListenerNames.DEBUG)

        if return_lambda is not None:
            input_type = internal_strings.InputTypes.DEBUG
        else:
            input_type = internal_strings.InputTypes.NO_INPUT
        return return_lambda, input_type

    def debug_command(self, command):
        """Finds the debug command corresponding to the string inputted. Returns either the command (as a function,
        needing a maze game instance to be passed to it), or None, if it could not find a corresponding command."""
        command_split = command.split(' ')
        command_name = command_split[0]
        if command_name in config.DebugCommands:
            command_args = tools.qlist(command_split[1:], except_val='')
            special_input = commands.get_command(command_name)
            return lambda maze_game: special_input.do(maze_game, command_args)
        else:
            self.invalid_input()
            return None

    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.overlay(strings.Play.INVALID_INPUT, end='\n')
        self.overlay.flush()


class Input(base.BaseIO):
    """Handles receiving user input."""

    def __init__(self, listeners):
        self.listeners = listeners
        self.enabled_listeners = []
        super(Input, self).__init__()

    def __call__(self, listener_name=None, *args, **kwargs):
        with self.enable_listener(listener_name) if listener_name is not None else tools.WithNothing():
            return self.enabled_listener(*args, **kwargs)

    def register_interface(self, interface):
        for listener in self.listeners.values():
            listener.register_interface(interface)
        super(Input, self).register_interface(interface)

    def add_listener(self, listener_name):
        listener = self.listeners[listener_name]
        self.enabled_listeners.append(listener)

    def remove_listener(self, listener_name):
        if self.enabled_listeners[-1].name == listener_name:
            self.enabled_listeners.pop()
        else:
            raise exceptions.ListenerRemovalException(strings.Input.Exceptions.INVALID_LISTENER_REMOVAL.format(listener=listener_name))

    def enable_listener(self, listener_name):
        """Enables the listener with the specified name, and disable the currently enabled listener. The currently
        enabled listener will be restored afterwards. Used with a with statement."""

        class EnableOnlyListener(tools.WithAnder):
            def __enter__(self_enable):
                self.add_listener(listener_name)

            def __exit__(self_enable, exc_type, exc_val, exc_tb):
                if exc_type is None or not issubclass(exc_type, exceptions.LeaveGameException):
                    self.remove_listener(listener_name)

        return EnableOnlyListener()

    @property
    def enabled_listener(self):
        if len(self.enabled_listeners) == 0:
            raise exceptions.ProgrammingException(strings.Input.Exceptions.NO_LISTENER)
        return self.enabled_listeners[-1]
