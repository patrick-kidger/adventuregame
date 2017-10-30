import config.config as config

import program.misc.helpers as helpers


class Entity(helpers.HasPositionMixin, helpers.appearance_from_filename(config.ENTITY_FOLDER)):
    """Generic entity base class."""
    incorporeal = False  # Whether this entity can pass through walls
    flight = False  # Whether this entity can fly. Duh.
    appearance_filename = 'entity.png'
    
    def __init__(self):
        super(Entity, self).__init__()
        
        
class Player(Entity):
    """Holds all player data."""
    appearance_filename = 'player.png'
