import sys
import Tools as tools


import Game.config.config as config

import Game.program.game as game
import Game.program.interface.base as base
import Game.program.interface.interface as interface_
import Game.program.interface.input as input_
import Game.program.interface.output as output

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
    # Output
    menu_font = base.Font(font_name=config.MENU_FONT_NAME, font_size=config.MENU_FONT_SIZE,
                          font_color=config.MENU_FONT_COLOR)
    debug_font = base.Font(font_name=config.DEBUG_FONT_NAME, font_size=config.DEBUG_FONT_SIZE,
                           font_color=config.DEBUG_FONT_COLOR)

    menu_overlay = output.MenuOverlay(name='menu',
                                      location=config.GRAPHICS_SCREEN_LOC,
                                      size=config.GRAPHICS_SCREEN_SIZE,
                                      background_color=config.MENU_BACKGROUND_COLOR,
                                      font=menu_font)
    game_overlay = output.GraphicsOverlay(name='game',
                                          location=config.GRAPHICS_SCREEN_LOC,
                                          size=config.GRAPHICS_SCREEN_SIZE,
                                          background_color=config.GRAPHICS_BACKGROUND_COLOR)
    debug_overlay = output.TextOverlay(name='debug',
                                       location=config.DEBUG_SCREEN_LOC,
                                       size=config.DEBUG_SCREEN_SIZE,
                                       background_color=config.DEBUG_BACKGROUND_COLOR,
                                       font=debug_font)
    overlays = tools.OrderedObject()
    overlays.debug = debug_overlay  # Done after object creation to ensure they are in the correct order.
    overlays.menu = menu_overlay    #
    overlays.game = game_overlay    #
    output_instance = output.Output(overlays)

    # Input
    menu_listener = input_.MenuListener(name='menu', overlay=menu_overlay)
    game_listener = input_.PlayListener(name='game')
    debug_listener = input_.DebugListener(name='debug', overlay=debug_overlay)
    listeners = tools.Object(menu=menu_listener, game=game_listener, debug=debug_listener)
    input_instance = input_.Input(listeners)

    # Interface
    interface = interface_.Interface(input_instance, output_instance)
    return interface


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'mapeditor':
        map_editor.start()
    else:
        play_game()
