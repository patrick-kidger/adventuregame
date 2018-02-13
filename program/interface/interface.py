import Tools as tools


import Game.config.config as config

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class Interface:
    def __init__(self, overlays):
        self.overlays = overlays
        interface_overlayer = InterfaceOverlayer(self)
        for overlay in overlays.values():
            overlay.register_interface(interface_overlayer)
        self._selected_overlay = [None]

        self.screen = sdl.display.set_mode(config.SCREEN_SIZE)
        sdl.event.set_grab(True)
        self.screen_size = self.screen.get_rect()
        self._inner_rect = sdl.Rect(config.SCREEN_EDGE_WIDTH, config.SCREEN_EDGE_WIDTH,
                                    self.screen_size.width - 2 * config.SCREEN_EDGE_WIDTH,
                                    self.screen_size.height - 2 * config.SCREEN_EDGE_WIDTH)
        sdl.display.set_caption(config.WINDOW_NAME)

    def reset(self, overlay_to_reset=None):
        """Resets and disables all overlays. If passed an argument, it will instead reset (and not disable) just that
        overlay."""
        if overlay_to_reset is None:
            self._selected_overlay = [None]
            for overlay in self.overlays.values():
                overlay.reset()
                overlay.disable()
        else:
            self.overlays[overlay_to_reset].reset()

    @property
    def selected_overlay(self):
        if self.overlays.debug.listen_enabled:
            return self.overlays.debug
        else:
            return [x for x in self._selected_overlay if x is None or x.listen_enabled][-1]

    @selected_overlay.setter
    def selected_overlay(self, value):
        if value is self.overlays.debug:
            self.overlays.debug.enable_listener()
        elif value is not self.selected_overlay:
            self.overlays.debug.disable_listener()
            if self.selected_overlay is not None and self.selected_overlay.must_be_top:
                self.selected_overlay.disable()
            try:
                self._selected_overlay.remove(value)
            except ValueError:
                pass
            self._selected_overlay.append(value)

    def out(self, overlay_name, *args, **kwargs):
        self.overlays[overlay_name].output(*args, **kwargs)

    def inp(self):
        inp_results = []

        # First get a list of events, and insert events for any keys we're listening to
        events = sdl.event.get(10, discard_old=True)

        events_to_handle = []
        pressed_keys = sdl.key.get_pressed()
        pressed_mouse = sdl.mouse.get_pressed()
        if self.selected_overlay is not None:
            listened_keys = {x for x in self.selected_overlay.listen_keys if pressed_keys[x.key]}
            listened_mouse = {x for x in self.selected_overlay.listen_mouse if pressed_mouse[x - 1]}
        else:
            listened_keys = set()
            listened_mouse = set()

        for event in events:
            # Avoid duplication
            if sdl.event.is_key(event) and event.key in (x.key for x in listened_keys):
                continue
            elif sdl.event.is_mouse(event, valid_buttons=listened_mouse) and event.type == sdl.MOUSEBUTTONDOWN:
                continue
            elif event.type != sdl.NOEVENT:
                events_to_handle.append(event)
        for listen_key in listened_keys:
            events_to_handle.append(sdl.event.Event(sdl.KEYDOWN, unicode=listen_key.unicode, key=listen_key.key))
        mouse_pos = sdl.mouse.get_pos()
        for listen_mouse in listened_mouse:
            events_to_handle.append(sdl.event.Event(sdl.MOUSEBUTTONDOWN, button=listen_mouse, pos=mouse_pos))
        events_to_handle.append(sdl.event.Event(sdl.MOUSEPRESENCE, pos=mouse_pos))

        # Now run through all the events we're handling this tick
        for event in events_to_handle:
            handled = False

            # Handle opening the debug console
            if sdl.event.is_key(event):
                if event.unicode == config.OPEN_CONSOLE:
                    self.overlays.debug.toggle()
                    handled = True
                if event.unicode == config.SELECT_CONSOLE and self.overlays.debug.screen_enabled:
                    self.overlays.debug.toggle_listener()
                    handled = True

            # Change which overlay is selected for text input
            if event.type == sdl.MOUSEBUTTONDOWN:
                for overlay in self.overlays.values():
                    if overlay.screen_enabled and overlay.location.collidepoint(event.pos):
                        overlay.enable_listener()
                        self.selected_overlay = overlay
                        break

            # Here we let the various overlays try to handle the event.
            if not handled:
                inp_result = None
                # If it's a mouse event...
                if sdl.event.is_mouse(event):
                    for overlay in self.overlays.values():
                        # ... work through all the overlays that the mouse is over, in order
                        if overlay.listen_enabled and overlay.location.collidepoint(event.pos):
                            try:
                                # Let the overlay try to handle it
                                inp_result = overlay.handle(event)
                            except exceptions.UnhandledInput:
                                # Let the next overlay try instead
                                pass
                            else:
                                break
                # If it's not (probably a text event) ...
                else:
                    # ... let the selected overlay try to handle it.
                    if self.selected_overlay is not None and self.selected_overlay.listen_enabled:
                        try:
                            inp_result = self.selected_overlay.handle(event)
                        except exceptions.UnhandledInput:
                            pass
                if inp_result is not None:
                    inp_results.append(inp_result)
        return inp_results

    def flush(self):
        """Pushes the changes from the overlays to the main screen."""
        for overlay in list(self.overlays.values())[::-1]:  # Reverse order, so the topmost stuff is blitted last.
            if overlay.screen_enabled:
                overlay.screen.update_cutouts()
                self.screen.blit(overlay.screen, overlay.location)

        sdl.display.update()

    def use(self, overlay_name):
        return self.use_background(overlay_name) + self.select_overlay(overlay_name)

    def use_background(self, overlay_name):
        overlay = self.overlays[overlay_name]
        return tools.set_context_variables(overlay, ('screen_enabled', 'listen_enabled'))

    def select_overlay(self, overlay_name):
        overlay = self.overlays[overlay_name]
        return tools.set_context_variables(self, ('selected_overlay',), overlay)


class InterfaceOverlayer:
    def __init__(self, interface):
        self._interface = interface

    def _get_overlay(self, overlay_name):
        return self._interface.overlays[overlay_name]

    def enable_overlay_background(self, overlay_name):
        self._get_overlay(overlay_name).enable()

    def enable_overlay(self, overlay_name):
        self.enable_overlay_background(overlay_name)
        self._interface.selected_overlay = self._get_overlay(overlay_name)

    def disable_overlay(self, overlay_name):
        self._get_overlay(overlay_name).disable()
