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
    """An abstract base class for listeners.

    Listeners are how the user passes input to the game. They are polled via the class Input, which keeps track of them
    all.

    Subclasses of this should define a method '_handle(self, event)', accepting a pygame event, that determines what
    should happen as a result of the event. The method _handle should not request further user input or wait in loops;
    instead it should store its current state in instance attributes which can then be used the next time _handle is
    called. If _handle returns something other than None, then this return value will be passed to the program.
    Typically this should be a 2-tuple; the first element passing the data that the program needs, and the second
    element an internal_strings.InputTypes attribute defining what kind of input type it is.

    Subclasses may also define a method 'reset', which should be used to reset the values of instance attributes to what
    they are initialised to. (It is obviously not necessarily appropriate for all instance attributes to go here; it's
    really only those attributes which are modified during _handle which need to be reset.)
    """
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
            if self.out.overlays.debug.enabled:
                self.inp.add_listener('debug')
            else:
                self.inp.remove_listener('debug')
            handled = True

        if char == config.SELECT_CONSOLE and self.out.overlays.debug.enabled:
            self.inp.toggle_listener('debug')
            handled = True

        if not handled:
            _inp_result = self._handle(event)
            if _inp_result is not None:
                inp_result = _inp_result
        return inp_result

    def reset(self):
        """Resets the listener back to its initialised state."""
        # Endpoint for super calls.


class OverlayListener(BaseListener):
    """Base class for listeners that associates an overlay with a listener."""
    def __init__(self, overlay, *args, **kwargs):
        self.overlay = overlay
        super(OverlayListener, self).__init__(*args, **kwargs)


class MenuListener(OverlayListener):
    """A listener for interacting with interface elements - buttons and things."""
    def __init__(self, *args, **kwargs):
        self.clicked_element = None
        super(MenuListener, self).__init__(*args, **kwargs)

    def reset(self):
        self.inp_result = {}, internal_strings.InputTypes.MENU
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
                    element_pos = menu_element.screen_pos(event.pos)
                    click_result = menu_element.click(element_pos)
                    # Stores its result
                    self.inp_result[0][menu_element] = click_result

                    # If we clicked a submit element
                    if menu_element in self.overlay.submit_elements:
                        # Make sure all necessary elements have data
                        for necessary_element in self.overlay.necessary_elements:
                            if self.inp_result[0].get(necessary_element, None) is None:
                                break  # Necessary element doesn't have data
                        else:
                            # All necessary elements have data; we're done here.
                            self.inp_result_ready = True
                    break
        if self.inp_result_ready:
            return self.inp_result


class PlayListener(BaseListener):
    """The listener for the main playing of the game - moving the player character and so forth."""
    def _handle(self, event):
        char, key_code = sdl.text_event(event)
        if char in config.Move:
            return config.Move.Direction[char], internal_strings.InputTypes.MOVEMENT


class TextListener(OverlayListener):
    """A listener for inputting text."""
    def reset(self):
        self.text = ''
        super(TextListener, self).reset()

    def _modify_text(self, event):
        """Modifies the instance's 'text' attribute based on pygame text event input."""
        char, key_code = sdl.text_event(event)

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


class DebugListener(TextListener):
    """The listener specifically for the debug console."""
    def __init__(self, *args, **kwargs):
        super(DebugListener, self).__init__(*args, **kwargs)
        self.text_memory = tools.nonneg_deque([], config.CONSOLE_MEMORY_SIZE)
        self.text_memory_cursor = -1

    def reset(self):
        if self.out is not None:  # When reset is called initially then the output hasn't been setup yet.
            self.overlay(config.CONSOLE_PROMPT)
        super(DebugListener, self).reset()

    def _handle(self, event):
        char, key_code = sdl.text_event(event)

        if key_code in (sdl.K_UP, sdl.K_DOWN):
            k_i = {sdl.K_UP: 1, sdl.K_DOWN: -1}
            moved_text_memory_cursor = tools.clamp(self.text_memory_cursor + k_i[key_code],
                                                   -1, config.CONSOLE_MEMORY_SIZE)
            try:
                text_from_memory = self.text_memory[moved_text_memory_cursor]
            except IndexError:
                pass
            else:
                self.overlay('\b' * len(self.text))
                self.text = text_from_memory
                self.text_memory_cursor = moved_text_memory_cursor
                self.overlay(self.text)
        else:
            if char is not None:  # Don't want the usual stream of no-events to reset things
                self.text_memory_cursor = -1

            if key_code in sdl.K_ENTER:
                if self.text != '':
                    self.text_memory.appendleft(self.text)
                self.overlay('\n')
                self._debug_command()
            elif key_code == sdl.K_ESCAPE:
                self.overlay.enabled = False
                self.inp.remove_listener('debug')
            else:
                self._modify_text(event)

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


class Input(base.BaseIO):
    """Handles receiving user input. Input should be requested by calling an instance of this class. What listener is
    enabled can be changed through this class's methods. Internally, instances of this class keep a list of listeners,
    with the topmost listener being the one that input is requested from. Subsequently enabling other listeners will
    then be added to the end of the list.

    Trying to disable a listener that is not the currently enabled listener - i.e. is not the topmost listener - will
    result in an exception.

    Note that the debug listener is handled specially, so that if it is enabled, it is always at the top of the list, so
    any other listeners that are subsequently enabled will be added to the list directly before the debug listener.
    This is useful because debug commands may wish to change the state of the game in quite complicated ways, and in
    particular change the listeners - and the debug console should remain usable whilst doing so, rather than become
    inoperative because of adding these extra listeners on top."""

    def __init__(self, listeners, *args, **kwargs):
        self._listeners = listeners
        self.maze_game = None
        self.reset()
        super(Input, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Call to request input from the currently enabled listener."""
        return self.enabled_listener(*args, **kwargs)

    def reset(self):
        """Resets this class back to its initialised state."""
        self._debug_listener_enabled = False  # Debug listener is handled specially so that it's always at the top
        self._enabled_listeners = []
        for listener in self._listeners.values():
            listener.reset()

    def register_interface(self, interface):
        for listener in self._listeners.values():
            listener.register_interface(interface)
        super(Input, self).register_interface(interface)

    def register_game(self, maze_game):
        """Lets the instance know what game instance it is being used with. This is needed for executing debug
        commands."""
        self.maze_game = maze_game

    def add_listener(self, listener_name):
        """Enables the specified listener."""
        if listener_name == 'debug':
            self._debug_listener_enabled = True
        else:
            listener = self._listeners[listener_name]
            self._enabled_listeners.append(listener)

    def remove_listener(self, listener_name):
        """Disables the specified listener."""
        if listener_name == 'debug':
            self._debug_listener_enabled = False
        else:
            if self._is_top_listener(listener_name):
                self._enabled_listeners.pop()
            else:
                raise exceptions.ListenerRemovalException(internal_strings.Exceptions.INVALID_LISTENER_REMOVAL.format(listener=listener_name))

    def toggle_listener(self, listener_name):
        """Toggles the specified listener, i.e. enables it if is disabled, and vice versa."""
        if listener_name == 'debug':
            self._debug_listener_enabled = not self._debug_listener_enabled
        else:
            if self._is_top_listener(listener_name):
                self.remove_listener(listener_name)
            else:
                self.add_listener(listener_name)

    def use(self, listener_name):
        """Enables the specified listener within a particular context, and disables it afterwards. Used in a with
        statement."""

        class EnableOnlyListener(tools.WithAdder):
            def __enter__(self_enable):
                self.add_listener(listener_name)

            def __exit__(self_enable, exc_type, exc_val, exc_tb):
                self.remove_listener(listener_name)

        return EnableOnlyListener()

    def _is_top_listener(self, listener_name):
        """Returns True if the specified listener is at the top of list of enabled listeners (ignoring the special case
        of the debug listener). Else returns False."""
        return len(self._enabled_listeners) != 0 and self._top_listener.name == listener_name

    @property
    def enabled_listener(self):
        """The currently enabled listener that is at the top of the list of listeners."""
        if self._debug_listener_enabled:
            return self._listeners.debug
        else:
            return self._top_listener

    @property
    def _top_listener(self):
        """The currently enabled listener that is at the top of the list of listeners, ignoring the special case of the
        debug listener."""
        if len(self._enabled_listeners) == 0:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.NO_LISTENER)
        return self._enabled_listeners[-1]

