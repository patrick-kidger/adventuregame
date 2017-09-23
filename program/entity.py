import Maze.config.config as config
import Maze.program.misc.helpers as helpers

class Entity(helpers.HasPositionMixin):
    """Generic entity base class."""
    display=config.ENTITY_DISPLAY
    incorporeal = False
    flight = False
    vision = 8
    
    def __init__(self):
        super(Entity, self).__init__()
        
    def disp(self):
        return self.display
        
        
class Player(Entity):
    """Holds all player data."""
    display=config.PLAYER_DISPLAY
