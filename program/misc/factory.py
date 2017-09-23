import Tools as tools

import Maze.data.maps as maps_
import Maze.program.game as game
import Maze.program.misc.interface as interface_


def maze_game_factory(start_game=True):
    """Creates a maze game."""
    interface = interface_factory()
    maps_access = maps_.MapsAccess()
    again = start_game
    while again:
        maze_game = game.MazeGame(maps_access, interface)        
        again = maze_game.start()
    return maze_game
    
def interface_factory():
    """Convenience function to set up the input and outputs of an interface."""
    input_ = interface_.BaseInput()
    output = interface_.Output()
    interface = interface_.Interface(input_, output)
    return interface