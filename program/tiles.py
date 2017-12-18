import Tools as tools


import Game.config.config as config
import Game.config.internal_strings as internal_strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.helpers as helpers


def all_tiles():
    omit_tiles = (Ceiling, Boundary)
    return {key: val for key, val in Tile.subclasses().items() if val not in omit_tiles}


class Tile(helpers.appearance_from_filename(config.TILE_FOLDER),
           tools.HasPositionMixin,
           tools.dynamic_subclassing_by_attr('definition'),
           tools.NoneAttributesMixin):
    """Represents a single empty tile of the map."""
    definition = ' '  # Uniquely identifies this class of tile; used when saving and loading maps
    appearance_filename = 'empty.png'  # The name of the image file for this type of tile. An 'appearance' attribute is
                                       # then automagically added. It will be a Surface that actually contains the
                                       # image.
    solid = False     # Whether corporeal entities cannot pass through it
    floor = False     # Whether entities can move downwards through it vertically
    ceiling = False   # Whether entities can move upwards through it vertically
    suspend = False   # Whether flightless entities should fall through it
    boundary = False  # Whether every entity cannot pass through it
    opaque = False    # Whether entities can see through it
    can_rotate = False  # Whether it makes sense to rotate this tile (e.g. doesn't make sense to rotate an empty tile;
                        # it does make sense to rotate an angled wall
    
    def __init__(self, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.entities = []
        
    def set_from_data(self, single_tile_data):
        """Sets this tile based on the loaded data."""
        try:
            self.pick_subclass(single_tile_data)
        except KeyError:
            raise exceptions.NoTileDefinitionException(internal_strings.Exceptions.NO_TILE_DEFINITION.format(definition=single_tile_data))


size = Tile.appearance.get_rect().width  # assumed to equal Tile.appearance.get_rect().height


class Rotatable:
    """Base class for rotatable tiles."""
    _instance_properties = dict(rotation=internal_strings.TileRotation.UP)
    can_rotate = True

            
class Floor(Tile):
    """Corporeal entitites cannot move downwards through this tile."""
    definition = '.'
    appearance_filename = 'floor.png'
    floor = True


class Ceiling(Tile):
    """Corporeal entitites cannot move upwards through this tile."""
    definition = "'"
    ceiling = True
    
            
class Wall(Floor, Ceiling):
    """Corporeal entities cannot move through this tile."""
    definition = 'W'
    appearance_filename = 'wall.png'
    solid = True
    opaque = True


class AngledWall(Rotatable, Wall):
    """A triangular wall."""
    definition = 'A'
    appearance_filename = 'angled_wall.png'


class ConcaveWall(Rotatable, Wall):
    """A wall that is curved outwards."""
    definition = 'Cc'
    appearance_filename = 'concave_wall.png'


class ConvexWall(Rotatable, Wall):
    """A wall that is curved inwards."""
    definition = 'Cv'
    appearance_filename = 'convex_wall.png'


class DoubleConcaveWall(Rotatable, Wall):
    """A wall that is curved strongly inwards."""
    definition = 'DCc'
    appearance_filename = 'double_concave_wall.png'


class DoubleConvexWall(Rotatable, Wall):
    """A wall that is curved strongly outwards."""
    definition = 'DCv'
    appearance_filename = 'double_convex_wall.png'


class Boundary(Floor, Ceiling):
    """Represents a wall that is never passable."""
    definition = 'B'
    boundary = True

    
class Stair(Tile):
    """Flightless entities can use these to move vertically upwards and downwards"""
    definition = 'X'
    appearance_filename = 'bothstair.png'
    suspend = True
    
    
class Upstair(Stair, Floor):
    """Flightless entities can use these to move vertically upwards. Corporeal entities cannot move vertically
    downwards."""
    definition = '>'
    appearance_filename = 'upstair.png'
    
    
class Downstair(Stair, Ceiling):
    """Flightless entities can use these to move vertically downwards. Corporeal entities cannot move vertically
    upwards."""
    definition = '<'
    appearance_filename = 'downstair.png'
