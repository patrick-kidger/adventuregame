import collections
import Tools as tools


import Game.config.config as config
import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.interface.base as base
import Game.program.misc.commands as commands
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class BaseListener(base.BaseIO):
    """An abstract base class for listeners.

    Listeners are how the user passes input to the game. They are polled via the class Input, which keeps track of them
    all.

    Subclasses of this should define a method '_handle(self, event)', accepting a pygame event, that determines what
    should happen as a result of the event. The method _handle should not request further user input or wait in loops;
    instead it should store its current state in instance attributes which can then be used the next time _handle is
    called. If _handle returns something other than None, then this return value will be passed to the program.
    Typically this should be a 2-tuple; the first element passing the data that the program needs, and the second
    element an internal.InputTypes attribute defining what kind of input type it is.

    Subclasses may also define a method 'reset', which should be used to reset the values of instance attributes to what
    they are initialised to. (It is obviously not necessarily appropriate for all instance attributes to go here; it's
    really only those attributes which are modified during _handle which need to be reset.)
    """

    def __init__(self, name, *args, **kwargs):
        super(BaseListener, self).__init__(*args, **kwargs)
        self.name = name
        self._listen_keys = set()
        self.reset()

    def __call__(self):
        inp_results = []

        events_to_handle = []
        pressed_keys = sdl.key.get_pressed()
        listened_keys = {x for x in self._listen_keys if pressed_keys[x.key]}
        events = sdl.event.get(10, discard_old=True)
        for event in events:
            if sdl.event.is_key(event) and event.key in (x.key for x in listened_keys):
                continue
            else:
                events_to_handle.append(event)
        for listen_key in listened_keys:
            events_to_handle.append(sdl.event.Event(sdl.KEYDOWN, unicode=listen_key.unicode, key=listen_key.key))

        for event in events_to_handle:
            handled = False

            if sdl.event.is_key(event):
                if event.unicode == config.OPEN_CONSOLE:
                    self.out.overlays.debug.toggle()
                    if self.out.overlays.debug.enabled:
                        self.inp.add_listener('debug')
                    else:
                        self.inp.remove_listener('debug')
                    handled = True
                if event.unicode == config.SELECT_CONSOLE and self.out.overlays.debug.enabled:
                    self.inp.toggle_listener('debug')
                    handled = True

            if not handled:
                inp_result = self._handle(event)
                if inp_result is not None:
                    inp_results.append(inp_result)
        return inp_results

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

    def reset(self):
        # The last element that we clicked
        self._clicked_element = None
        # Whether we are currently still clicking the element. (i.e. we are in between mousedown and mouseup)
        self._mouse_is_down = False
        # The current state of all the menu elements
        self._menu_results = collections.defaultdict(lambda: None)
        super(MenuListener, self).reset()

    def _handle(self, event):
        if sdl.event.is_mouse(event, valid_buttons=(1, 4, 5)):
            if event.type == sdl.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return self._left_click(event)
                elif event.button in (4, 5):  # Scroll wheel
                    menu_element = self._find_element(event.pos)
                    if menu_element is not None:
                        element_pos = menu_element.screen_pos(event.pos)
                        is_scroll_up = (event.button == 4)
                        menu_element.scroll(element_pos, is_scroll_up)

            elif event.type == sdl.MOUSEBUTTONUP:
                self._mouse_is_down = False

                if self._clicked_element is not None:
                    element_pos = self._clicked_element.screen_pos(event.pos)
                    self._clicked_element.mouseup(element_pos)

            elif event.type == sdl.MOUSEMOTION:
                if self._mouse_is_down and self._clicked_element is not None:
                    element_pos = self._clicked_element.screen_pos(event.pos)
                    self._clicked_element.mousemotion(element_pos)

    def _left_click(self, event):
        """Handles left clicking on a menu element. Pulled out as a separate function for clarity."""

        self._mouse_is_down = True

        # Unclick the previous menu element
        if self._clicked_element is not None:
            self._clicked_element.un_mousedown()

        menu_element = self._find_element(event.pos)
        if menu_element is not None:
            # Click this menu element
            self._clicked_element = menu_element
            element_pos = menu_element.screen_pos(event.pos)
            click_result = menu_element.mousedown(element_pos)
            # Stores its result
            self._menu_results[menu_element] = click_result

            can_submit = False
            # If we clicked a submit element
            if menu_element in self.overlay.submit_elements:
                # Make sure all necessary elements have data
                for necessary_element in self.overlay.necessary_elements:
                    if self._menu_results[necessary_element] is None:
                        break  # Necessary element doesn't have data
                else:
                    # All necessary elements have data; we're done here.
                    can_submit = True
            elif menu_element in self.overlay.back_elements:
                can_submit = True

            if can_submit:
                menu_results = self._menu_results
                self.reset()
                return menu_results, internal.InputTypes.MENU

    def _find_element(self, pos):
        """Returns the menu element that the given position is over, or None if it is not over any menu element."""
        for menu_element in self.overlay.menu_elements:
            if menu_element.screen.point_within_offset(pos):
                return menu_element


class PlayListener(BaseListener):
    """The listener for the main playing of the game - moving the player character and so forth."""
    _input_to_action = {sdl.key.code(config.Move.UP): internal.Move.UP,
                        sdl.key.code(config.Move.DOWN): internal.Move.DOWN,
                        sdl.key.code(config.Move.LEFT): internal.Move.LEFT,
                        sdl.key.code(config.Move.RIGHT): internal.Move.RIGHT,
                        sdl.key.code(config.Action.VERTICAL_UP): internal.Action.VERTICAL_UP,
                        sdl.key.code(config.Action.VERTICAL_DOWN): internal.Action.VERTICAL_DOWN}

    def __init__(self, *args, **kwargs):
        super(PlayListener, self).__init__(*args, **kwargs)
        listen_codes = (sdl.key.code(key_name) for key_name in config.Move.values())
        # Normally I'd use tools.Object here, but they're not hashable.
        Key = collections.namedtuple('Key', ['unicode', 'key'])
        self._listen_keys.update(Key(unicode=sdl.key.name(code), key=code) for code in listen_codes)

    def _handle(self, event):
        if sdl.event.is_key(event):
            try:
                return self._input_to_action[event.key], internal.InputTypes.ACTION
            except KeyError:
                return None


class TextListener(OverlayListener):
    """A listener for inputting text."""
    def reset(self):
        self.text = ''
        super(TextListener, self).reset()

    def _modify_text(self, event):
        """Modifies the overlays's 'text' attribute based on pygame text event input."""
        if sdl.event.is_key(event):
            should_output = True
            if event.key == sdl.K_BACKSPACE:
                # Disable outputting backspaces if we're not actually modifying the text with them.
                if len(self.text) == 0:
                    should_output = False
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

            if should_output:
                self.overlay(event.unicode)


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
        if sdl.event.is_key(event):
            if event.key in (sdl.K_UP, sdl.K_DOWN):
                k_i = {sdl.K_UP: 1, sdl.K_DOWN: -1}
                moved_text_memory_cursor = tools.clamp(self.text_memory_cursor + k_i[event.key],
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
                self.text_memory_cursor = -1

                if event.key in sdl.K_ENTER:
                    if self.text != '':
                        self.text_memory.appendleft(self.text)
                    self.overlay('\n')
                    self._debug_command()
                elif event.key == sdl.K_ESCAPE:
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
            print_result = command.do(self.inp.game_instance, command_args)
            if print_result is not None:
                self.overlay(print_result, end='\n')
        finally:
            self.reset()

    def invalid_input(self):
        """Gives an error message indicating that the input is invalid."""
        self.overlay(strings.Debug.INVALID_INPUT, end='\n')


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
        self.game_instance = None
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

    def register_game(self, game_instance):
        """Lets the instance know what game instance it is being used with. This is needed for executing debug
        commands."""
        self.game_instance = game_instance

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
                raise exceptions.ListenerRemovalException(strings.Exceptions.INVALID_LISTENER_REMOVAL.format(listener=listener_name))

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
            raise exceptions.ProgrammingException(strings.Exceptions.NO_LISTENER)
        return self._enabled_listeners[-1]

