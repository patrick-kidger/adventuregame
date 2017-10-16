import Tools as tools

import Maze.config.config as config
import Maze.program.misc.helpers as helpers


DefinitionSubclassing = tools.dynamic_subclassing_by_attr('definition')
AppearanceFromFilename = helpers.appearance_from_filename(config.TILE_FOLDER)

class TileMetaclass(DefinitionSubclassing.__class__, AppearanceFromFilename.__class__):
    pass

class Tile(helpers.HasPositionMixin,
           tools.NoneAttributesMixin,
           DefinitionSubclassing,
           AppearanceFromFilename,
           metaclass=TileMetaclass):
    """Represents a single tile of the map."""
    definition = ' '  # The character used when defining a map to use this tile
    appearance_filename = 'empty.png'  # The name of the image file for this type of tile. The metaclass will
                                       # automagically add an 'appearance' attribute that is a Surface that actually
                                       # contains the image.
    solid = False     # Whether corporeal entities cannot pass through it
    floor = False     # Whether entities can move downwards through it vertically
    ceiling = False   # Whether entities can move upwards through it vertically
    suspend = False   # Whether flightless entities should fall through it
    boundary = False  # Whether every entity cannot pass through it
    opaque = False    # Whether entities cannot see through it
    
    def __init__(self, **kwargs):
        self.entities = []
        super(Tile, self).__init__(**kwargs)
        
    def set_from_data(self, single_tile_data):
        """Sets this tile based on the loaded data."""
        self.pick_subclass(single_tile_data)


class Tile2(Tile):
    """Exactly the same as Tile, just with a different definition. When the parser reads a .map file, it strips all
    leading whitespace - which might include spaces that are meant to mean empty tiles. This allows for explicitly
    setting empty tiles as the first tile on a line in the .map file."""
    definition = '.'

            
class Floor(Tile):
    """Corporeal entitites cannot move downwards through this tile."""
    definition = '+'
    appearance_filename = 'floor.png'
    floor = True


class Ceiling(Tile):
    """Corporeal entitites cannot move upwards through this tile."""
    definition = "'"
    ceiling = True
    
            
class Wall(Floor, Ceiling):
    """Corporeal entities cannot move through this tile."""
    _instance_properties = dict(adjacent_walls=set(), appearance=None)
    definition = 'W'
    solid = True
    opaque = True
    wall = True  # Denotes that its visuals should affect, and be affected by, adjacent walls.

    wall_codes = {frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN, config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): 'wall_udlr.png',
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN, config.WallAdjacency.LEFT                            ]): 'wall_udl.png',
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN,                            config.WallAdjacency.RIGHT]): 'wall_udr.png',
                  frozenset([config.WallAdjacency.UP,                            config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): 'wall_ulr.png',
                  frozenset([                         config.WallAdjacency.DOWN, config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): 'wall_dlr.png',
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN                                                       ]): 'wall_ud.png',
                  frozenset([config.WallAdjacency.UP,                            config.WallAdjacency.LEFT                            ]): 'wall_ul.png',
                  frozenset([                         config.WallAdjacency.DOWN, config.WallAdjacency.LEFT                            ]): 'wall_dl.png',
                  frozenset([config.WallAdjacency.UP,                                                       config.WallAdjacency.RIGHT]): 'wall_ur.png',
                  frozenset([                         config.WallAdjacency.DOWN,                            config.WallAdjacency.RIGHT]): 'wall_dr.png',
                  frozenset([                                                    config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): 'wall_lr.png',
                  frozenset([config.WallAdjacency.UP                                                                                  ]): 'wall_u.png',
                  frozenset([                         config.WallAdjacency.DOWN                                                       ]): 'wall_d.png',
                  frozenset([                                                    config.WallAdjacency.LEFT                            ]): 'wall_l.png',
                  frozenset([                                                                               config.WallAdjacency.RIGHT]): 'wall_r.png',
                  frozenset([                                                                                                         ]): 'wall_column.png'}
    
    def convert_wall(self):    
        """Sets this tile to a custom visual based on adjacent walls."""
        adjacent_walls = frozenset(self.adjacent_walls)
        self.appearance_filename = self.wall_codes[adjacent_walls]
        self.update_appearance()

        
class FakeWall(Wall):
    """Looks like a wall, but corporeal entites can move through it."""
    definition = 'F'
    solid = False
    
    
class InvisibleWall(Tile):
    """Looks like an empty tile, but corporeal entities cannot move through it."""
    definition = 'I'
    solid = True
        
        
class Boundary(Wall):
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
