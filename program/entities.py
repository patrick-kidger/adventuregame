import Tools as tools


import Game.config.config as config

import Game.program.tiles as tiles
import Game.program.misc.helpers as helpers


class Entity(helpers.HasAppearances, tools.HasPositionMixin, appearance_files_location=config.ENTITY_FOLDER):
    """Generic entity base class."""

    incorporeal = False  # Whether this entity can pass through walls
    flight = False  # Whether this entity can fly. Duh.
    appearance_filenames = 'entity.png'

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)

        # fall_speed physics ticks have to have gone by, recorded in fall_counter, before falling another z-level
        self.fall_counter = 0
        self.fall_speed = config.FALL_TICKS

        self.speed = config.DEFAULT_ENTITY_SPEED

        self.radius = self.appearance.get_rect().height / 2

    @property
    def topleft_x(self):
        return self.pos.x - self.radius

    @property
    def topleft_y(self):
        return self.pos.y - self.radius


class Player(Entity):
    """Holds all player data."""
    appearance_filenames = 'player.png'
