import Tools as tools

import config.config as config
import config.internal_strings as internal_strings

import data.maps as maps_

import program.game as game

import program.interface.interface as interface_
import program.interface.input as input_
import program.interface.output as output


def maze_game_factory(start_game=True):
    """Creates a maze game."""
    interface = interface_factory()
    maps_access = maps_.MapsAccess()
    maze_game = game.MazeGame(maps_access, interface)
    again = maze_game.start() if start_game else False
    while again:
        maze_game = game.MazeGame(maps_access, interface)
        again = maze_game.start()
    return maze_game


def interface_factory():
    """Convenience function to set up the input and outputs of an interface."""
    # Output
    game_overlay = output.GraphicsOverlay(name=internal_strings.OverlayNames.GAME,
                                          location=config.GRAPHICS_SCREEN_LOC,
                                          size=config.GRAPHICS_SCREEN_SIZE,
                                          background_color=config.GRAPHICS_BACKGROUND_COLOR)
    debug_overlay = output.TextOverlay(name=internal_strings.OverlayNames.DEBUG,
                                       location=config.DEBUG_SCREEN_LOC,
                                       size=config.DEBUG_SCREEN_SIZE,
                                       background_color=config.DEBUG_BACKGROUND_COLOR)
    overlays = tools.Object(from_dict={internal_strings.OverlayNames.GAME: game_overlay,
                                       internal_strings.OverlayNames.DEBUG: debug_overlay})
    output_ = output.Output(overlays)

    # Input
    game_listener = input_.PlayListener(name=internal_strings.ListenerNames.DEBUG)
    debug_listener = input_.DebugListener(name=internal_strings.ListenerNames.DEBUG, overlay=debug_overlay)
    listeners = tools.Object(from_dict={internal_strings.ListenerNames.GAME: game_listener,
                                        internal_strings.ListenerNames.DEBUG: debug_listener})
    input__ = input_.Input(listeners)

    # Interface
    interface = interface_.Interface(input__, output_)
    return interface
