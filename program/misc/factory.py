import Tools as tools

import Maze.config.config as config
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

    # Input
    game_listener = interface_.PlayListener(name=config.ListenerNames.DEBUG_NAME,
                                            enabled=False)
    debug_listener = interface_.TextListener(name=config.ListenerNames.DEBUG_NAME,
                                             enabled=True)
    listeners = tools.Object(from_dict={config.ListenerNames.GAME_NAME: game_listener,
                                        config.ListenerNames.DEBUG_NAME: debug_listener})
    input_ = interface_.Input(listeners)

    # Output
    game_overlay = interface_.GraphicsOverlay(name=config.OverlayNames.GAME_NAME,
                                              location=config.GRAPHICS_SCREEN_LOC,
                                              size=config.GRAPHICS_SCREEN_SIZE,
                                              background_color=config.GRAPHICS_BACKGROUND_COLOR,
                                              enabled=True)
    debug_overlay = interface_.TextOverlay(name=config.OverlayNames.DEBUG_NAME,
                                           location=config.DEBUG_SCREEN_LOC,
                                           size=config.DEBUG_SCREEN_SIZE,
                                           background_color=config.DEBUG_BACKGROUND_COLOR,
                                           enabled=False)
    overlays = tools.Object(from_dict={config.OverlayNames.GAME_NAME: game_overlay,
                                       config.OverlayNames.DEBUG_NAME: debug_overlay})
    output = interface_.Output(overlays)

    # Interface
    interface = interface_.Interface(input_, output)
    return interface
