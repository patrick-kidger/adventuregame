import Tools as tools

import Maze.program.misc.helpers as helpers
import Maze.config.config as config


class Tile(helpers.HasPositionMixin, tools.dynamic_subclassing_by_attr('definition'), tools.NoneAttributesMixin):
    """Represents a single tile of the map."""
    definition = ' '  # The character used when defining a map to use this tilea
    display = ' '     # How the tile appears in-game.
    solid = False     # Whether corporeal entities cannot pass through it
    floor = False     # Whether entities can move downwards through it vertically
    ceiling = False   # Whether entities can move upwards through it vertically
    suspend = False   # Whether flightless entities should fall through it
    boundary = False  # Whether every entity cannot pass through it
    opaque = False    # Whether entities cannot see through it
    
    def __init__(self, **kwargs):
        self.entities = []
        super(Tile, self).__init__(**kwargs)
        
    def __str__(self):
        return self.display
        
    def __repr__(self):
        return self.display
        
    def set_from_data(self, single_tile_data):
        """Sets this tile based on the loaded data."""
        self.pick_subclass(single_tile_data)
        
    def _setdisp(self, display):
        """Overrides what this tile is displayed as."""
        self.display = display
        
    def disp(self):
        """Determines what this tile will be displayed as."""
        if self.entities:
            return self.entities[0].disp()
        else:
            return self.display
            
    def add_entity(self, entity):
        """Adds an entity to this tile."""
        self.entities.append(entity)
        
    def remove_entity(self, entity):
        """Removes an entity from this tile."""
        self.entities.remove(entity)
            
            
class Floor(Tile):
    """Corporeal entitites cannot move downwards through this tile."""
    definition = '+'
    display = '+'
    floor = True


class Ceiling(Tile):
    """Corporeal entitites cannot move upwards through this tile."""
    definition = "'"
    display = ' '
    ceiling = True
    
            
class Wall(Floor, Ceiling):
    """Corporeal entities cannot move through this tile."""
    _subclass_properties = dict(adjacent_walls=set())
    definition = 'W'
    solid = True
    opaque = True
    wall = True  # Denotes that its visuals should affect, and be affected by, adjacent walls.

    wall_codes = {frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN, config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): config.WallChars.UDLR,
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN, config.WallAdjacency.LEFT                            ]): config.WallChars.UDL,
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN,                            config.WallAdjacency.RIGHT]): config.WallChars.UDR,
                  frozenset([config.WallAdjacency.UP,                            config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): config.WallChars.ULR,
                  frozenset([                         config.WallAdjacency.DOWN, config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): config.WallChars.DLR,
                  frozenset([config.WallAdjacency.UP, config.WallAdjacency.DOWN                                                       ]): config.WallChars.UD,
                  frozenset([config.WallAdjacency.UP,                            config.WallAdjacency.LEFT                            ]): config.WallChars.UL,
                  frozenset([                         config.WallAdjacency.DOWN, config.WallAdjacency.LEFT                            ]): config.WallChars.DL,
                  frozenset([config.WallAdjacency.UP,                                                       config.WallAdjacency.RIGHT]): config.WallChars.UR,
                  frozenset([                         config.WallAdjacency.DOWN,                            config.WallAdjacency.RIGHT]): config.WallChars.DR,
                  frozenset([                                                    config.WallAdjacency.LEFT, config.WallAdjacency.RIGHT]): config.WallChars.LR,
                  frozenset([config.WallAdjacency.UP                                                                                  ]): config.WallChars.U,
                  frozenset([                         config.WallAdjacency.DOWN                                                       ]): config.WallChars.D,
                  frozenset([                                                    config.WallAdjacency.LEFT                            ]): config.WallChars.L,
                  frozenset([                                                                               config.WallAdjacency.RIGHT]): config.WallChars.R,
                  frozenset([                                                                                                         ]): config.WallChars.COLUMN}
    
    def convert_wall(self):    
        """Sets this tile to a custom visual based on adjacent walls."""
        adjacent_walls = frozenset(self.adjacent_walls)
        self._setdisp(self.wall_codes[adjacent_walls])

        
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
    display = 'X'
    suspend = True
    
    
class Upstair(Stair, Floor):
    """Flightless entities can use these to move vertically upwards. Corporeal entities cannot move vertically
    downwards."""
    definition = '>'
    display = '>'
    
    
class Downstair(Stair, Ceiling):
    """Flightless entities can use these to move vertically downwards. Corporeal entities cannot move vertically
    upwards."""
    definition = '<'
    display = '<'
