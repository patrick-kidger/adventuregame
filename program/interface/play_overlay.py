import collections


import Game.config.config as config
import Game.config.internal as internal

import Game.program.interface.base as base
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


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
        # Normally I'd use tools.Object here, but they're not hashable.
        Key = collections.namedtuple('Key', ['unicode', 'key'])
        self.listen_keys.update(Key(unicode=sdl.key.name(code), key=code) for code in listen_codes)

    def handle(self, event):
        if sdl.event.is_key(event) and event.key in self._input_to_action:
            return self._input_to_action[event.key], internal.InputTypes.ACTION
        else:
            raise exceptions.UnhandledInput
