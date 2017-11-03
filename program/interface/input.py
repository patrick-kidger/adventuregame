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
        self.reset()

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

    def reset(self):
        pass


class OverlayListener(BaseListener):
    """Allows associating an overlay with a listener."""
    def __init__(self, overlay, *args, **kwargs):
        self.overlay = overlay
        super(OverlayListener, self).__init__(*args, **kwargs)


class MenuListener(OverlayListener):
    def __init__(self, *args, **kwargs):
        self.clicked_element = None
        super(MenuListener, self).__init__(*args, **kwargs)

    def reset(self):
        self._inp_result = {}, internal_strings.InputTypes.MENU
        self.inp_result_ready = False
        super(MenuListener, self).reset()

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
    def reset(self):
        self.text = ''
        super(TextListener, self).reset()

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
            self._debug_command()
        elif key_code == sdl.K_ESCAPE:
            self.overlay.enabled = False
            self.inp.remove_listener('debug')
        else:
            self._modify_text(char, key_code)

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
            command.do(self.inp.maze_game, command_args)
        finally:
            self.reset()

    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.overlay(strings.Play.INVALID_INPUT, end='\n')
        self.out.flush()


class Input(base.BaseIO):
    """Handles receiving user input."""

    def __init__(self, listeners, *args, **kwargs):
        self._listeners = listeners
        self.maze_game = None
        self.reset()
        super(Input, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.enabled_listener(*args, **kwargs)

    def reset(self):
        self.debug_listener_enabled = False  # Debug listener is handled specially so that it's always at the top
        self._enabled_listeners = []
        for listener in self._listeners.values():
            listener.reset()

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

    def toggle_listener(self, listener_name):
        if listener_name == 'debug':
            self.debug_listener_enabled = not self.debug_listener_enabled
        else:
            if self._is_top_listener(listener_name):
                self.remove_listener(listener_name)
            else:
                self.add_listener(listener_name)

    def use(self, listener_name):
        """Enables the listener with the specified name, and disable the currently enabled listener. The currently
        enabled listener will be restored afterwards. Used with a with statement."""

        class EnableOnlyListener(tools.WithAdder):
            def __enter__(self_enable):
                self.add_listener(listener_name)

            def __exit__(self_enable, exc_type, exc_val, exc_tb):
                self.remove_listener(listener_name)

        return EnableOnlyListener()

    def _is_top_listener(self, listener_name):
         return len(self._enabled_listeners) != 0 and self._top_listener.name == listener_name

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

