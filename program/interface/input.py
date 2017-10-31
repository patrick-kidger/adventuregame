import math
import Tools as tools


import config.config as config
import config.internal_strings as internal_strings
import config.strings as strings

import program.interface.base as base

import program.misc.commands as commands
import program.misc.exceptions as exceptions
import program.misc.helpers as helpers
import program.misc.sdl as sdl


class BaseListener(base.BaseIO, helpers.NameMixin):
    """An abstract base class for listeners."""
    def __init__(self, *args, **kwargs):
        self.inp_result = None, internal_strings.InputTypes.NO_INPUT
        super(BaseListener, self).__init__(*args, **kwargs)

    def __call__(self):
        self.inp_result = None, internal_strings.InputTypes.NO_INPUT

        first_pass = True
        while first_pass or self.repeat:
            first_pass = False
            handled = False
            done = False

            event = sdl.event_stream(single_event=True, discard_old=True)
            char, key_code = sdl.text_event(event)

            if char == config.OPEN_CONSOLE:
                self.out.overlays.debug.toggle()
                self.out.flush()
                handled = True

            if char in (config.OPEN_CONSOLE, config.SELECT_CONSOLE) and self.out.overlays.debug.enabled:
                self.inp.add_listener('debug')
                handled = True

            if not handled:
                done = self._handle(event)
            if done:  # For use with self.repeat=True.
                break
        return self.inp_result


class OverlayListener(BaseListener):
    """Allows associating an overlay with a listener."""
    def __init__(self, overlay, *args, **kwargs):
        self.overlay = overlay
        super(OverlayListener, self).__init__(*args, **kwargs)


class MenuListener(OverlayListener):
    repeat = True

    def _handle(self):
        pass


class PlayListener(BaseListener):
    repeat = False

    def _handle(self, event):
        char, key_code = sdl.text_event(event)
        if char in config.Move:
            self.inp_result = config.Move.Direction[char], internal_strings.InputTypes.MOVEMENT


class TextListener(OverlayListener):
    repeat = False

    def __init__(self, overlay, name, *args, **kwargs):
        self.text = ''
        super(TextListener, self).__init__(overlay, name, *args, **kwargs)

    def _modify_text(self, char, key_code):
        if char is not None:
            should_output = True
            if key_code == sdl.K_BACKSPACE:
                # Disable outputting backspaces if we're not actually modifying the tet with them.
                if len(self.text) == 0:
                    should_output = False
                self.text = self.text[:-1]
            else:
                self.text += char

            if should_output:
                self.overlay(char)
                self.overlay.flush()


class DebugListener(TextListener):
    def _handle(self, event):
        char, key_code = sdl.text_event(event)

        if key_code in sdl.K_ENTER:
            self.overlay('\n')
            self.overlay.flush()
            self.inp_result = self._debug_command(self.text), internal_strings.InputTypes.DEBUG
            self.text = ''
        elif key_code == sdl.K_ESCAPE:
            self.overlay.enabled = False
            self.inp.remove_listener('debug')
        else:
            self._modify_text(char, key_code)

    def _debug_command(self, command):
        """Finds the debug command corresponding to the string inputted. Returns either the command (as a function,
        needing a maze game instance to be passed to it), or None, if it could not find a corresponding command."""
        command_split = command.split(' ')
        command_name = command_split[0]
        if command_name in config.DebugCommands:
            command_args = tools.qlist(command_split[1:], except_val='')
            special_input = commands.get_command(command_name)
            return lambda maze_game: special_input.do(maze_game, command_args)
        else:
            self._invalid_input()
            return None

    def _invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.overlay(strings.Play.INVALID_INPUT, end='\n')
        self.overlay.flush()


class Input(base.BaseIO):
    """Handles receiving user input."""

    def __init__(self, listeners, *args, **kwargs):
        self.listeners = listeners
        self.enabled_listeners = []
        super(Input, self).__init__(*args, **kwargs)

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
            raise exceptions.ListenerRemovalException(internal_strings.Exceptions.INVALID_LISTENER_REMOVAL.format(listener=listener_name))

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
            raise exceptions.ProgrammingException(internal_strings.Exceptions.NO_LISTENER)
        return self.enabled_listeners[-1]
