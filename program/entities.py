import Tools as tools


import Game.config.config as config

import Game.program.tiles as tiles
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

        self.radius = self.appearance.get_rect().height / 2
        super(Entity, self).__init__(*args, **kwargs)

    @property
    def square_pos(self):
        square_pos = tools.Object()
        square_pos.x = int((self.pos.x + 0.5 * tiles.width) // tiles.width)
        square_pos.y = int((self.pos.y + 0.5 * tiles.height) // tiles.height)
        square_pos.z = self.pos.z
        return square_pos
        
        
class Player(Entity):
    """Holds all player data."""
    appearance_filename = 'player.png'
