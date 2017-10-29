import Tools as tools

import Maze.config.config as config
import Maze.config.internal_strings as internal_strings
import Maze.data.maps as maps_
import Maze.program.game as game
import Maze.program.misc.interface as interface_


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
    game_overlay = interface_.GraphicsOverlay(name=internal_strings.OverlayNames.GAME,
                                              location=config.GRAPHICS_SCREEN_LOC,
                                              size=config.GRAPHICS_SCREEN_SIZE,
                                              background_color=config.GRAPHICS_BACKGROUND_COLOR)
    debug_overlay = interface_.TextOverlay(name=internal_strings.OverlayNames.DEBUG,
                                           location=config.DEBUG_SCREEN_LOC,
                                           size=config.DEBUG_SCREEN_SIZE,
                                           background_color=config.DEBUG_BACKGROUND_COLOR)
    overlays = tools.Object(from_dict={internal_strings.OverlayNames.GAME: game_overlay,
                                       internal_strings.OverlayNames.DEBUG: debug_overlay})
    output = interface_.Output(overlays)

    # Input
    game_listener = interface_.PlayListener(name=internal_strings.ListenerNames.DEBUG)
    debug_listener = interface_.DebugListener(name=internal_strings.ListenerNames.DEBUG, overlay=debug_overlay)
    listeners = tools.Object(from_dict={internal_strings.ListenerNames.GAME: game_listener,
                                        internal_strings.ListenerNames.DEBUG: debug_listener})
    input_ = interface_.Input(listeners)

    # Interface
    interface = interface_.Interface(input_, output)
    return interface
