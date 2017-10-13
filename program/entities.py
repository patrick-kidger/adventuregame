import Maze.config.config as config
import Maze.program.misc.helpers as helpers


class Entity(helpers.HasPositionMixin, metaclass=helpers.appearance_metaclass(config.ENTITY_FOLDER)):
    """Generic entity base class."""
    display = config.ENTITY_DISPLAY  # Depreciated
    incorporeal = False  # Whether this entity can pass through walls
    flight = False  # Whether this entity can fly. Duh.
    appearance_filename = 'entity.png'
    
    def __init__(self):
        super(Entity, self).__init__()
        
    def disp(self):
        return self.display
        
        
class Player(Entity):
    """Holds all player data."""
    display = config.PLAYER_DISPLAY
    appearance_filename = 'player.png'
