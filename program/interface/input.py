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
        super(BaseListener, self).__init__(*args, **kwargs)

    def __call__(self):
        inp_result = None, internal_strings.InputTypes.NO_INPUT

        handled = False

        event = sdl.event_stream(single_event=True, discard_old=True)
        char, key_code = sdl.text_event(event)

        if char == config.OPEN_CONSOLE:
            self.out.overlays.debug.toggle()
            self.out.flush()

        if char == config.OPEN_CONSOLE or (char == config.SELECT_CONSOLE and self.out.overlays.debug.enabled):
            self.inp.toggle_listener('debug')
            handled = True

        if not handled:
            _inp_result = self._handle(event)
            if _inp_result is not None:
                inp_result = _inp_result
        return inp_result


class OverlayListener(BaseListener):
    """Allows associating an overlay with a listener."""
    def __init__(self, overlay, *args, **kwargs):
        self.overlay = overlay
        super(OverlayListener, self).__init__(*args, **kwargs)


class MenuListener(OverlayListener):
    def __init__(self, *args, **kwargs):
        self.clicked_element = None
        self.reset()
        super(MenuListener, self).__init__(*args, **kwargs)

    def reset(self):
        self._inp_result = {}, internal_strings.InputTypes.MENU
        self.inp_result_ready = False

    def _handle(self, event):
        if self.inp_result_ready:
            self.reset()

        if event.type == sdl.MOUSEBUTTONDOWN:
            # Unclick the previous menu element
            if self.clicked_element is not None:
                self.clicked_element.unclick()

            for menu_element in self.overlay.menu_elements:
                if menu_element.screen.point_within(event.pos):  # We interact with this menu element
                    # Click this menu element
                    self.clicked_element = menu_element
                    click_result = menu_element.click(event.pos)
                    # Stores its result
                    self._inp_result[0][menu_element] = click_result

                    # If we clicked a submit element
                    if menu_element in self.overlay.submit_elements:
                        # Make sure all necessary elements have data
                        for necessary_element in self.overlay.necessary_elements:
                            if self._inp_result[0].get(necessary_element, None) is None:
                                break  # Necessary element doesn't have data
                        else:
                            # All necessary elements have data; we're done here.
                            self.inp_result_ready = True
                    break
            self.out.flush()
        return self.inp_result

    @property
    def inp_result(self):
        return self._inp_result if self.inp_result_ready else None


class PlayListener(BaseListener):
    def _handle(self, event):
        char, key_code = sdl.text_event(event)
        if char in config.Move:
            return config.Move.Direction[char], internal_strings.InputTypes.MOVEMENT


class TextListener(OverlayListener):
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
                self.out.flush()


class DebugListener(TextListener):
    def _handle(self, event):
        char, key_code = sdl.text_event(event)

        if key_code in sdl.K_ENTER:
            self.overlay('\n')
            self.out.flush()
            command = self._debug_command(self.text)
            self.text = ''
            if command is not None:
                return command, internal_strings.InputTypes.DEBUG
        elif key_code == sdl.K_ESCAPE:
            self.overlay.enabled = False
            self.inp.remove_listener('debug')
        else:
            self._modify_text(char, key_code)
        return None, internal_strings.InputTypes.NO_INPUT

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
        self.out.flush()


class Input(base.BaseIO):
    """Handles receiving user input."""

    def __init__(self, listeners, *args, **kwargs):
        self._listeners = listeners
        self.maze_game = None
        self.clear()
        super(Input, self).__init__(*args, **kwargs)

    def __call__(self, listener_name=None, *args, **kwargs):
        with self.enable_listener(listener_name) if listener_name is not None else tools.WithNothing():
            input_result, input_type = self.enabled_listener(*args, **kwargs)
        if input_type == internal_strings.InputTypes.DEBUG:
            input_result(self.maze_game)
            return None, internal_strings.InputTypes.NO_INPUT
        else:
            return input_result, input_type

    def clear(self):
        self.debug_listener_enabled = False  # Debug listener is handled specially so that it's always at the top
        self._enabled_listeners = []

    def register_interface(self, interface):
        for listener in self._listeners.values():
            listener.register_interface(interface)
        super(Input, self).register_interface(interface)

    def register_game(self, maze_game):
        self.maze_game = maze_game

    def add_listener(self, listener_name):
        if listener_name == 'debug':
            self.debug_listener_enabled = True
        else:
            listener = self._listeners[listener_name]
            self._enabled_listeners.append(listener)

    def remove_listener(self, listener_name):
        if listener_name == 'debug':
            self.debug_listener_enabled = False
        else:
            if self._is_top_listener(listener_name):
                self._enabled_listeners.pop()
            else:
                raise exceptions.ListenerRemovalException(internal_strings.Exceptions.INVALID_LISTENER_REMOVAL.format(listener=listener_name))

    def _is_top_listener(self, listener_name):
         return len(self._enabled_listeners) != 0 and self._top_listener.name == listener_name

    def enable_listener(self, listener_name):
        """Enables the listener with the specified name, and disable the currently enabled listener. The currently
        enabled listener will be restored afterwards. Used with a with statement."""

        class EnableOnlyListener(tools.WithAdder):
            def __enter__(self_enable):
                self.add_listener(listener_name)

            def __exit__(self_enable, exc_type, exc_val, exc_tb):
                if exc_type is None or not issubclass(exc_type, exceptions.LeaveGameException):
                    self.remove_listener(listener_name)

        return EnableOnlyListener()

    def toggle_listener(self, listener_name):
        if listener_name == 'debug':
            self.debug_listener_enabled = not self.debug_listener_enabled
        else:
            if self._is_top_listener(listener_name):
                self.remove_listener(listener_name)
            else:
                self.add_listener(listener_name)

    @property
    def enabled_listener(self):
        if self.debug_listener_enabled:
            return self._listeners.debug
        else:
            return self._top_listener

    @property
    def _top_listener(self):
        if len(self._enabled_listeners) == 0:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.NO_LISTENER)
        return self._enabled_listeners[-1]

