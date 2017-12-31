import Tools as tools


import Game.config.config as config

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class Interface:
    def __init__(self, overlays):
        self.overlays = overlays
        self._selected_overlay = None

        self.screen = sdl.display.set_mode(config.SCREEN_SIZE)
        self.screen_size = self.screen.get_rect()
        sdl.display.set_caption(config.WINDOW_NAME)

    def register_game(self, game_instance):
        for overlay in self.overlays.values():
            overlay.register_game(game_instance)

    def reset(self, overlay_to_reset=None):
        """Resets and disables all overlays. If passed an argument, it will instead reset (and not disable) just that
        overlay."""
        if overlay_to_reset is None:
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
            return self._selected_overlay

    @selected_overlay.setter
    def selected_overlay(self, value):
        if value is self.overlays.debug:
            self.overlays.debug.enable_listener()
        else:
            self.overlays.debug.disable_listener()
            self._selected_overlay = value

    def out(self, overlay_name, *args, **kwargs):
        self.overlays[overlay_name].output(*args, **kwargs)

    def inp(self):
        inp_results = []

        # First get a list of events, and insert events for any keys we're listening to
        events_to_handle = []
        pressed_keys = sdl.key.get_pressed()
        if self.selected_overlay is not None:
            listened_keys = {x for x in self.selected_overlay.listen_keys if pressed_keys[x.key]}
        else:
            listened_keys = set()
        events = sdl.event.get(10, discard_old=True)
        for event in events:
            if sdl.event.is_key(event) and event.key in (x.key for x in listened_keys):
                # Avoid duplication
                continue
            elif event.type != sdl.NOEVENT:
                events_to_handle.append(event)
        for listen_key in listened_keys:
            events_to_handle.append(sdl.event.Event(sdl.KEYDOWN, unicode=listen_key.unicode, key=listen_key.key))

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

            # This looks a bit messy: here we let the various overlays try to handle the event.
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
                # If it's a text event...
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
        overlay = self.overlays[overlay_name]
        return tools.set_context_variables(overlay, ('screen_enabled', 'listen_enabled'))
