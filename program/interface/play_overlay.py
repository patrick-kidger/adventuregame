import collections


import Game.config.config as config
import Game.config.internal as internal

import Game.program.misc.exceptions as exceptions
import Game.program.misc.helpers as helpers
import Game.program.misc.sdl as sdl

import Game.program.interface.base as base


class PlayOverlay(base.GraphicsOverlay):
    _input_to_action = {sdl.key.code(config.Move.UP): internal.Move.UP,
                        sdl.key.code(config.Move.DOWN): internal.Move.DOWN,
                        sdl.key.code(config.Move.LEFT): internal.Move.LEFT,
                        sdl.key.code(config.Move.RIGHT): internal.Move.RIGHT,
                        sdl.key.code(config.Action.VERTICAL_UP): internal.Action.VERTICAL_UP,
                        sdl.key.code(config.Action.VERTICAL_DOWN): internal.Action.VERTICAL_DOWN}

    def __init__(self, *args, **kwargs):
        super(PlayOverlay, self).__init__(*args, **kwargs)
        listen_codes = (sdl.key.code(key_name) for key_name in config.Move.values())
        Key = collections.namedtuple('Key', ['unicode', 'key'])
        self.listen_keys.update(Key(unicode=sdl.key.name(code), key=code) for code in listen_codes)
        self.listen_mouse.add(3)
        self.screen_size = self.screen.get_rect()
        self._inner_rect = sdl.Rect(config.SCREEN_EDGE_WIDTH, config.SCREEN_EDGE_WIDTH,
                                    self.screen_size.width - 2 * config.SCREEN_EDGE_WIDTH,
                                    self.screen_size.height - 2 * config.SCREEN_EDGE_WIDTH)

    def _in_screen_edge(self, pos):
        return self.screen_size.collidepoint(pos) and not self._inner_rect.collidepoint(pos)

    def handle(self, event):
        if sdl.event.is_key(event):
            if event.key in self._input_to_action:
                return self._input_to_action[event.key], internal.InputTypes.ACTION
            elif event.key == sdl.K_ESCAPE:
                self._interface_overlayer.enable_overlay('escape')
        elif event.type == sdl.MOUSEPRESENCE and self._in_screen_edge(event.pos):
            return helpers.XYPos(x=event.pos[0], y=event.pos[1]), internal.InputTypes.MOVE_CAMERA
        elif event.type == sdl.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            return helpers.XYPos(x=event.pos[0], y=event.pos[1]), internal.InputTypes.MOVE_ABS
        else:
            raise exceptions.UnhandledInput
