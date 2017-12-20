import Tools as tools


import Game.config.config as config

import Game.program.tiles as tiles
import Game.program.misc.helpers as helpers


class Entity(helpers.HasAppearances, tools.HasPositionMixin, appearance_files_location=config.ENTITY_FOLDER):
    """Generic entity base class."""

    incorporeal = False  # Whether this entity can pass through walls
    flight = False  # Whether this entity can fly. Duh.
    appearance_filenames = {None: 'entity.png'}

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)

        # fall_speed physics ticks have to have gone by, recorded in fall_counter, before falling another z-level
        self.fall_counter = 0
        self.fall_speed = config.FALL_TICKS

        self.speed = config.DEFAULT_ENTITY_SPEED

        self.radius = self.appearance.get_rect().height / 2

    @property
    def center_x(self):
        return self.pos.x + 0.5 * tiles.size

    @center_x.setter
    def center_x(self, val):
        self.pos.x = val - 0.5 * tiles.size

    @property
    def center_y(self):
        return self.pos.y + 0.5 * tiles.size

    @center_y.setter
    def center_y(self, val):
        self.pos.y = val - 0.5 * tiles.size

    @property
    def center_pos(self):
        return tools.Object(x=self.center_x, y=self.center_y)

    @property
    def square_pos(self):
        square_pos = tools.Object()
        square_pos.x = int(self.center_x // tiles.size)
        square_pos.y = int(self.center_y // tiles.size)
        square_pos.z = self.pos.z
        return square_pos
        
        
class Player(Entity):
    """Holds all player data."""
    appearance_filenames = {None: 'player.png'}
