import collections
import Tools as tools


import Game.config.config as config
import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.helpers as helpers
import Game.program.misc.sdl as sdl


def all_tiles():
    """List all tiles that make sense to be placed."""

    # Omit the abstract tiles (and Boundary, which is special as always being at the edge of the map).
    omit_tiles = (TileBase, Rotatable, Boundary)
    return {key: val for key, val in TileBase.subclasses().items() if val not in omit_tiles}


class TileBase(helpers.HasAppearances, tools.HasPositionMixin, tools.SubclassTrackerMixin(),
               appearance_files_location=config.TILE_FOLDER, tracking_attr='definition'):
    """Base class for all tiles. Subclasses should:
    - Define an appearance. This is done either by setting a string type 'appearance_filename' attribute, or by setting
    a collections.OrderedDict type 'appearance_filenames' attribute."""

    solid = False         # Whether corporeal entities cannot pass through it
    floor = False         # Whether entities can move downwards through it vertically
    suspend_up = False    # Whether flightless entities can move upwards from this tile. (e.g. stairs)
    suspend_down = False  # Whether flightless entities can move downwards from this tile.
    boundary = False      # Whether every entity cannot pass through it
    can_rotate = False    # Whether it makes sense to rotate this tile (e.g. doesn't make sense to rotate an empty tile;
                          # it does make sense to rotate an angled wall.)


class Empty(TileBase):
    """Represents a single empty tile of the map."""

    definition = ''  # Uniquely identifies this class of tile; used when saving and loading maps. Cannot contain spaces.
    # The name of the image file for this type of tile. An 'appearance' property is then automagically added.
    appearance_filenames = 'empty.png'


_tile_size = Empty.appearances[None].get_rect()
size = _tile_size.width
if size != _tile_size.height:
    raise exceptions.ProgrammingException(strings.Exceptions.NON_SQUARE_TILE)


class Rotatable(TileBase):
    """Base class for rotatable tiles."""

    can_rotate = True

    def __init_subclass__(cls, **kwargs):
        super(Rotatable, cls).__init_subclass__(**kwargs)

        # Create rotations of all its appearances, if they need updating.
        if 'appearance_filenames' in cls.__dict__:
            cls.left_appearances = collections.OrderedDict()
            cls.down_appearances = collections.OrderedDict()
            cls.right_appearances = collections.OrderedDict()
            for key, appearance in cls.appearances.items():
                cls.left_appearances[key] = sdl.transform.rotate(appearance, 90)
                cls.down_appearances[key] = sdl.transform.rotate(appearance, 180)
                cls.right_appearances[key] = sdl.transform.rotate(appearance, -90)

    @property
    def unrotated_appearance(self):
        """The object's unrotated appearance."""
        if self.appearance_lookup is helpers._sentinel:
            raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
        return self.appearances[self.appearance_lookup]

    @property
    def left_appearance(self):
        """The object's appearance rotated 90 degrees anticlockwise."""
        if self.appearance_lookup is helpers._sentinel:
            raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
        return self.left_appearances[self.appearance_lookup]

    @property
    def down_appearance(self):
        """The object's appearance rotated 180 degrees."""
        if self.appearance_lookup is helpers._sentinel:
            raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
        return self.down_appearances[self.appearance_lookup]

    @property
    def right_appearance(self):
        """The object's appearance rotated 90 degrees clockwise."""
        if self.appearance_lookup is helpers._sentinel:
            raise exceptions.ProgrammingException(strings.Exceptions.NO_APPEARANCE_LOOKUP)
        return self.right_appearances[self.appearance_lookup]

    # Rebind appearance to the rotated appearance
    @property
    def appearance(self):
        """The object's rotated appearance"""
        rotated_appearance = {internal.TileRotation.UP: self.unrotated_appearance,
                              internal.TileRotation.RIGHT: self.right_appearance,
                              internal.TileRotation.DOWN: self.down_appearance,
                              internal.TileRotation.LEFT: self.left_appearance}
        return rotated_appearance[self.rotation]

    def __init__(self, **kwargs):
        super(Rotatable, self).__init__(**kwargs)
        self.rotation = internal.TileRotation.UP

    def next_rotate(self):
        """Rotates the tile 90 degrees clockwise."""

        next_rotations = {internal.TileRotation.UP: internal.TileRotation.RIGHT,
                          internal.TileRotation.RIGHT: internal.TileRotation.DOWN,
                          internal.TileRotation.DOWN: internal.TileRotation.LEFT,
                          internal.TileRotation.LEFT: internal.TileRotation.UP}
        self.rotation = next_rotations[self.rotation]

            
class Floor(TileBase):
    """Corporeal entities cannot move downwards through this tile."""

    definition = '.'
    appearance_filenames = 'floor.png'
    floor = True


class FloorlessWall(Rotatable, TileBase):
    """Corporeal entities cannot move horizontally through this tile."""

    definition = 'f'
    appearance_filenames = collections.OrderedDict(
        [(internal.Geometry.ANGLED, 'angled_wall_empty.png'),
         (internal.Geometry.CONCAVE, 'concave_wall_empty.png'),
         (internal.Geometry.CONVEX, 'convex_wall_empty.png'),
         (internal.Geometry.CIRCLE, 'circle_wall_empty.png'),
         (internal.Geometry.DOUBLE_CONCAVE, 'double_concave_wall_empty.png'),
         (internal.Geometry.DOUBLE_CONVEX, 'double_convex_wall_empty.png')])
    solid = True

    def __init__(self, **kwargs):
        super(FloorlessWall, self).__init__(**kwargs)
        self.geometry = self.appearance_lookup


class Wall(Floor, FloorlessWall):
    """Corporeal entities cannot move horizontally or downwards through this tile."""

    definition = 'W'
    appearance_filenames = collections.OrderedDict(
        [(internal.Geometry.SQUARE, 'wall.png'),
         (internal.Geometry.ANGLED, 'angled_wall.png'),
         (internal.Geometry.CONCAVE, 'concave_wall.png'),
         (internal.Geometry.CONVEX, 'convex_wall.png'),
         (internal.Geometry.CIRCLE, 'circle_wall.png'),
         (internal.Geometry.DOUBLE_CONCAVE, 'double_concave_wall.png'),
         (internal.Geometry.DOUBLE_CONVEX, 'double_convex_wall.png')])


class Boundary(TileBase):
    """Represents a wall that is never passable, to any entity, ever."""

    definition = 'B'
    appearance_filenames = 'boundary.png'
    boundary = True

    
class Stair(TileBase):
    """Flightless entities can use these to move vertically upwards and downwards."""

    definition = 'X'
    appearance_filenames = collections.OrderedDict(
        [(frozenset([internal.StairDirection.VERTICAL_UP,
                     internal.StairDirection.VERTICAL_DOWN]), 'bothstair_empty.png'),
         (frozenset([internal.StairDirection.VERTICAL_UP]), 'upstair_empty.png'),
         (frozenset([internal.StairDirection.VERTICAL_DOWN]), 'downstair_empty.png'),
         (frozenset(), 'nostair_empty.png')])

    def __init__(self, **kwargs):
        super(Stair, self).__init__(**kwargs)
        self.suspend_up = (internal.StairDirection.VERTICAL_UP in self.appearance_lookup)
        self.suspend_down = (internal.StairDirection.VERTICAL_DOWN in self.appearance_lookup)


class FloorStair(Floor, Stair):
    """Flightless entities can use these to move vertically upwards. They block movement by corporeal entities
    downwards."""

    definition = '>'
    appearance_filenames = collections.OrderedDict(
        [(frozenset([internal.StairDirection.VERTICAL_UP]), 'upstair.png'),
         (frozenset(), 'nostair.png')])
