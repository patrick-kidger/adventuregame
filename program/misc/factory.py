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
    input_ = interface_.BaseInput()
    output = interface_.Output(game=interface_.GraphicsOverlay(config.GRAPHICS_SCREEN_LOC, config.GRAPHICS_SCREEN_SIZE),
                               debug=interface_.TextOverlay(config.DEBUG_SCREEN_LOC, config.DEBUG_SCREEN_SIZE))
    interface = interface_.Interface(input_, output)
    return interface
