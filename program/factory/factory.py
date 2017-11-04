import Tools as tools


import config.config as config

import data.maps as maps_

import program.game as game
import program.interface.base as base
import program.interface.interface as interface_
import program.interface.input as input_
import program.interface.output as output


def maze_game_factory(start_game=True):
    """Creates a maze game."""
    interface = interface_factory()
    maps_access = maps_.MapsAccess()
    maze_game = game.MazeGame(maps_access, interface)
    if start_game:
        maze_game.start()
    return maze_game


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
    overlays = tools.OrderedObject(game=game_overlay)
    overlays.menu = menu_overlay    # Done after object creation to ensure they are in the correct order.
    overlays.debug = debug_overlay  # Top overlay last
    output_ = output.Output(overlays)

    # Input
    menu_listener = input_.MenuListener(name='menu', overlay=menu_overlay)
    game_listener = input_.PlayListener(name='game')
    debug_listener = input_.DebugListener(name='debug', overlay=debug_overlay)
    listeners = tools.Object(menu=menu_listener, game=game_listener, debug=debug_listener)
    input__ = input_.Input(listeners)

    # Interface
    interface = interface_.Interface(input__, output_)
    return interface
