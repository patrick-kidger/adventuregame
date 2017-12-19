import collections
import Tools as tools


import Game.config.config as config
import Game.config.internal_strings as internal_strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.helpers as helpers
import Game.program.misc.sdl as sdl


def all_tiles():
    omit_tiles = (Tile, Rotatable, Boundary)
    return {key: val for key, val in Tile.subclasses().items() if val not in omit_tiles}


def set_from_data(tile_data, pos):
    try:
        tile_class = Tile.find_subclass(tile_data)
    except KeyError:
        raise exceptions.NoTileDefinitionException(internal_strings.Exceptions.NO_TILE_DEFINITION.format(definition=tile_data))
    else:
        return tile_class(pos=pos)


class Tile(helpers.appearance_from_filename(config.TILE_FOLDER),
           tools.HasPositionMixin,
           tools.subclass_tracker('definition')):
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
                        # it does make sense to rotate an angled wall.)


size = Tile.appearance.get_rect().width  # assumed to equal Tile.appearance.get_rect().height


class Rotatable(Tile):
    """Base class for rotatable tiles."""
    can_rotate = True

    def __init__(self, **kwargs):
        super(Rotatable, self).__init__(**kwargs)
        self.rotation = internal_strings.TileRotation.UP

    def __init_subclass__(cls, **kwargs):
        super(Tile, cls).__init_subclass__(**kwargs)
        if hasattr(cls, 'appearances'):
            cls.left_appearances = collections.OrderedDict()
            cls.down_appearances = collections.OrderedDict()
            cls.right_appearances = collections.OrderedDict()
            for key, appearance in cls.appearances.items():
                cls.left_appearances[key] = sdl.transform.rotate(appearance, 90)
                cls.down_appearances[key] = sdl.transform.rotate(appearance, 180)
                cls.right_appearances[key] = sdl.transform.rotate(appearance, -90)

            cls.left_appearance = property(lambda self: self.left_appearances[self.appearance_lookup])
            cls.down_appearance = property(lambda self: self.down_appearances[self.appearance_lookup])
            cls.right_appearance = property(lambda self: self.right_appearances[self.appearance_lookup])
        else:
            cls.left_appearance = sdl.transform.rotate(cls.appearance, 90)
            cls.down_appearance = sdl.transform.rotate(cls.appearance, 180)
            cls.right_appearance = sdl.transform.rotate(cls.appearance, -90)

    @property
    def rotated_appearance(self):
        if self.can_rotate:
            rot_appearance = {internal_strings.TileRotation.UP: self.appearance,
                              internal_strings.TileRotation.RIGHT: self.right_appearance,
                              internal_strings.TileRotation.DOWN: self.down_appearance,
                              internal_strings.TileRotation.LEFT: self.left_appearance}
            return rot_appearance[self.rotation]
        else:
            return self.appearance

            
class Floor(Tile):
    """Corporeal entitites cannot move downwards through this tile."""
    definition = '.'
    appearance_filename = 'floor.png'
    floor = True


class FloorlessWall(Rotatable, Tile):
    """Corporeal entities cannot move through this tile."""
    definition = 'f'
    appearance_filenames = collections.OrderedDict(
        [(internal_strings.Geometry.ANGLED, 'angled_wall_empty.png'),
         (internal_strings.Geometry.CONCAVE, 'concave_wall_empty.png'),
         (internal_strings.Geometry.CONVEX, 'convex_wall_empty.png'),
         (internal_strings.Geometry.CIRCLE, 'circle_wall_empty.png'),
         (internal_strings.Geometry.DOUBLE_CONCAVE, 'double_concave_wall_empty.png'),
         (internal_strings.Geometry.DOUBLE_CONVEX, 'double_convex_wall_empty.png')])
    solid = True
    opaque = True


class Wall(Floor, FloorlessWall):
    definition = 'W'
    appearance_filenames = collections.OrderedDict(
        [(internal_strings.Geometry.SQUARE, 'wall.png'),
         (internal_strings.Geometry.ANGLED, 'angled_wall.png'),
         (internal_strings.Geometry.CONCAVE, 'concave_wall.png'),
         (internal_strings.Geometry.CONVEX, 'convex_wall.png'),
         (internal_strings.Geometry.CIRCLE, 'circle_wall.png'),
         (internal_strings.Geometry.DOUBLE_CONCAVE, 'double_concave_wall.png'),
         (internal_strings.Geometry.DOUBLE_CONVEX, 'double_convex_wall.png')])


class Boundary(Tile):
    """Represents a wall that is never passable."""
    definition = 'B'
    boundary = True

    
class Stair(Tile):
    """Flightless entities can use these to move vertically upwards and downwards."""
    definition = 'X'
    appearance_filenames = collections.OrderedDict(
        [(frozenset([internal_strings.StairAdjacency.VERTICAL_UP,
                     internal_strings.StairAdjacency.VERTICAL_DOWN]), 'bothstair_empty.png'),
         (frozenset([internal_strings.StairAdjacency.VERTICAL_UP]), 'upstair_empty.png'),
         (frozenset([internal_strings.StairAdjacency.VERTICAL_DOWN]), 'downstair_empty.png'),
         (frozenset(), 'nostair_empty.png')])
    suspend = True


class FloorStair(Floor, Stair):
    """Flightless entities can use these to move vertically upwards, but not downwards."""
    definition = '>'
    appearance_filenames = collections.OrderedDict(
        [(frozenset([internal_strings.StairAdjacency.VERTICAL_UP]), 'upstair.png'),
         (frozenset(), 'nostair.png')])
