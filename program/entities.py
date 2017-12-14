import Game.config.config as config

import Game.program.misc.helpers as helpers


class Entity(helpers.HasPositionMixin, helpers.appearance_from_filename(config.ENTITY_FOLDER)):
    """Generic entity base class."""
    incorporeal = False  # Whether this entity can pass through walls
    flight = False  # Whether this entity can fly. Duh.
    appearance_filename = 'entity.png'

    def __init__(self, *args, **kwargs):
        # fall_speed physics ticks have to have gone by, recorded in fall_counter, before falling another z-level
        self.fall_counter = 0
        self.fall_speed = config.FALL_TICKS

        self.speed = config.DEFAULT_ENTITY_SPEED
        super(Entity, self).__init__(*args, **kwargs)
        
        
class Player(Entity):
    """Holds all player data."""
    appearance_filename = 'player.png'
