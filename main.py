import sys
import Tools as tools


import Game.config.config as config

import Game.program.game as game
import Game.program.interface.base as base
import Game.program.interface.interface as interface
import Game.program.interface.menu_overlay as menu_overlay
import Game.program.interface.play_overlay as play_overlay
import Game.program.interface.text_overlay as text_overlay

import Game.tools.map_editor as map_editor


def play_game(start_game=True):
    """Creates a game instance."""
    interface = interface_factory()
    game_instance = game.MainGame(interface)
    if start_game:
        game_instance.start()
    return game_instance


def interface_factory():
    """Convenience function to set up the input and outputs of an interface."""
    # Fonts
    menu_font = base.font(config.MENU_FONT, config.MENU_FONT_SIZE, config.MENU_FONT_COLOR)
    debug_font = base.font(config.DEBUG_FONT, config.DEBUG_FONT_SIZE, config.DEBUG_FONT_COLOR)

    # Overlays
    menu_overlay_ = menu_overlay.MenuOverlay(name='menu',
                                             location=config.GRAPHICS_SCREEN_LOC,
                                             size=config.GRAPHICS_SCREEN_SIZE,
                                             background_color=config.MENU_BACKGROUND_COLOR,
                                             font=menu_font)
    game_overlay = play_overlay.PlayOverlay(name='game',
                                            location=config.GRAPHICS_SCREEN_LOC,
                                            size=config.GRAPHICS_SCREEN_SIZE,
                                            background_color=config.GRAPHICS_BACKGROUND_COLOR)
    debug_overlay = text_overlay.DebugOverlay(name='debug',
                                              location=config.DEBUG_SCREEN_LOC,
                                              size=config.DEBUG_SCREEN_SIZE,
                                              background_color=config.DEBUG_BACKGROUND_COLOR,
                                              font=debug_font)
    overlays = tools.OrderedObject()
    overlays.debug = debug_overlay  # Done after object creation to ensure they are in the correct order.
    overlays.menu = menu_overlay_   #
    overlays.game = game_overlay    #

    # Interface
    interface_ = interface.Interface(overlays)
    return interface_


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'mapeditor':
        map_editor.start()
    else:
        play_game()
