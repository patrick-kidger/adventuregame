import collections
import math
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


class TileBase(helpers.HasAppearances, tools.HasPositionMixin, tools.SubclassTrackerMixin('definition'),
               appearance_files_location=config.TILE_FOLDER):
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

    def __init__(self, **kwargs):
        super(TileBase, self).__init__(**kwargs)
        self._geom_rect = sdl.Rect(self.x * size, self.y * size, size, size)

    def wall_collide(self, entity, pos):
        """Whether or not the given entity at the given position will collide with this tile's wall."""
        # If the tile has a wall to collide with
        if self.boundary or (self.solid and not entity.incorporeal):
            # And the entity collides with the square that is the tile
            if self._wall_geom_collide(entity, pos):
                # Then the entity collides with the wall
                return True
        return False

    def floor_collide(self, entity, pos):
        """Whether or not the given entity at the given position will collide (i.e. can stand on) this tile's wall."""
        # If the tile has a floor to collide with
        if self.floor and not entity.incorporeal:
            # And the entity collides with the square that is the tile
            if self._floor_geom_collide(entity, pos):
                # Then the entity collides with the floor
                return True
        return False

    def suspend_collide(self, entity, pos):
        """Whether or not the given entity at the given position will collide (i.e. can hold on to) this tile's
        suspension."""
        # If the tile has a suspension to collide with
        if self.suspend_up or self.suspend_down:
            # And the entity collides with the square that is the tile
            if self._wall_geom_collide(entity, pos):
                # Then the entity collides with the suspension
                return True
        # A bit special: incorporeal entities shouldn't just fall through the floor to the bottom of the world, so
        # we let them count floors as suspensions.
        if self.floor and entity.incorporeal:
            if self._floor_geom_collide(entity, pos):
                return True
        return False

    def _wall_geom_collide(self, entity, pos):
        """Whether or not the given entity at the given position intersects with the wall geometry of the tile."""
        entity_circle = tools.Disc(entity.radius, pos)
        return entity_circle.colliderect(self._geom_rect)

    def _floor_geom_collide(self, entity, pos):
        """Whether or not the given entity at the given position intersects with the floor geometry of the tile."""
        entity_circle = tools.Disc(entity.radius, pos)
        return entity_circle.colliderect(self._geom_rect)


class Empty(TileBase):
    """Represents a single empty tile of the map."""

    definition = ''  # Uniquely identifies this class of tile; used when saving and loading maps. Cannot contain spaces.
    # The name of the image file for this type of tile. An 'appearance' property is then automagically added.
    appearance_filenames = 'empty.png'


_tile_size = Empty.appearances[None].get_rect()
size = _tile_size.width
if size != _tile_size.height:
    raise exceptions.ProgrammingException(strings.Exceptions.NON_SQUARE_TILE)
diag = math.sqrt(2) * size


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

    def __init__(self, rotation=internal.TileRotation.UP, **kwargs):
        self.rotation = rotation
        super(Rotatable, self).__init__(**kwargs)

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


class Wall(Rotatable, Floor, TileBase):
    """Corporeal entities cannot move horizontally or downwards through this tile.

    The tile's floor extends all the way to the edge of the square."""

    definition = 'W'
    appearance_filenames = collections.OrderedDict(
        [(internal.Geometry.SQUARE, 'wall.png'),
         (internal.Geometry.RECTANGLE, 'rectangle_wall.png'),
         (internal.Geometry.ANGLED, 'angled_wall.png'),
         (internal.Geometry.CONCAVE, 'concave_wall.png'),
         (internal.Geometry.CONVEX, 'convex_wall.png'),
         (internal.Geometry.CIRCLE, 'circle_wall.png'),
         (internal.Geometry.DOUBLE_CONCAVE, 'double_concave_wall.png'),
         (internal.Geometry.DOUBLE_CONVEX, 'double_convex_wall.png')])
    solid = True

    # Just to collect the different collision functions together.
    # Note that as these are accessed via lookup and then called, 'self' will not refer to CollisionFunctions, and must
    # be passed as an argument. Which is a bit ugly - the 'natural' way to do this would need better support for
    # anonymous functions than Python has.
    class CollisionFunctions:
        def square(self, entity_circle):
            return entity_circle.colliderect(self._geom_rect)

        def rectangle(self, entity_circle):
            return entity_circle.colliderect(self._geom_rect)

        def angled(self, entity_circle):
            return entity_circle.collide_irat(self._geom_irat)

        def concave(self, entity_circle):
            collide_interior = entity_circle.colliderect(self._geom_rect) and not \
                entity_circle.collide_disc(self._geom_circle)
            return collide_interior or entity_circle.collide_arc(self._geom_arc)

        def convex(self, entity_circle):
            return entity_circle.colliderect(self._geom_rect) and entity_circle.collide_disc(self._geom_circle)

        def circle(self, entity_circle):
            return entity_circle.collide_disc(self._geom_circle)

        def double_concave(self, entity_circle):
            collide_interior = entity_circle.colliderect(self._geom_rect) and not \
                entity_circle.collide_disc(self._geom_circle)
            return collide_interior or entity_circle.collide_arc(self._geom_arc)

        def double_convex(self, entity_circle):
            return entity_circle.colliderect(self._geom_rect) and entity_circle.collide_disc(self._geom_circle)

        lookup = {internal.Geometry.SQUARE: square, internal.Geometry.ANGLED: angled,
                  internal.Geometry.CONCAVE: concave, internal.Geometry.CONVEX: convex,
                  internal.Geometry.CIRCLE: circle, internal.Geometry.DOUBLE_CONCAVE: double_concave,
                  internal.Geometry.DOUBLE_CONVEX: double_convex, internal.Geometry.RECTANGLE: rectangle}

    def __init__(self, **kwargs):
        super(Wall, self).__init__(**kwargs)
        self.geometry = self.appearance_lookup

        # Here we consider all the possible geometries and rotations and set up the geometric objects that are used to
        # determine collisions. By necessity, then, this is a little involved.
        if self.geometry in {internal.Geometry.RECTANGLE, internal.Geometry.DOUBLE_CONCAVE}:
            if self.rotation == internal.TileRotation.UP:
                self._geom_rect = sdl.Rect(self.x * size, self.y * size, size, size * 0.5)
            elif self.rotation == internal.TileRotation.LEFT:
                self._geom_rect = sdl.Rect(self.x * size, self.y * size, size * 0.5, size)
            elif self.rotation == internal.TileRotation.DOWN:
                self._geom_rect = sdl.Rect(self.x * size, (self.y + 0.5) * size, size, size * 0.5)
            elif self.rotation == internal.TileRotation.RIGHT:
                self._geom_rect = sdl.Rect((self.x + 0.5) * size, self.y * size, size * 0.5, size)
            else:
                raise exceptions.ProgrammingException

        if self.geometry == internal.Geometry.ANGLED:
            if self.rotation == internal.TileRotation.UP:
                irat_kwargs = {'pos': helpers.XYPos(x=(self.x + 1) * size, y=(self.y + 1) * size), 'upleft': True}
            elif self.rotation == internal.TileRotation.LEFT:
                irat_kwargs = {'pos': helpers.XYPos(x=(self.x + 1) * size, y=self.y * size), 'downleft': True}
            elif self.rotation == internal.TileRotation.DOWN:
                irat_kwargs = {'pos': helpers.XYPos(x=self.x * size, y=self.y * size), 'downright': True}
            elif self.rotation == internal.TileRotation.RIGHT:
                irat_kwargs = {'pos': helpers.XYPos(x=self.x * size, y=(self.y + 1) * size), 'upright': True}
            else:
                raise exceptions.ProgrammingException
            self._geom_irat = tools.Irat(size, **irat_kwargs)

        if self.geometry in {internal.Geometry.CONCAVE, internal.Geometry.CONVEX, internal.Geometry.CIRCLE,
                        internal.Geometry.DOUBLE_CONCAVE, internal.Geometry.DOUBLE_CONVEX}:
            if self.geometry in {internal.Geometry.CONCAVE, internal.Geometry.CONVEX}:
                x_offset = int(self.rotation in {internal.TileRotation.RIGHT, internal.TileRotation.DOWN})
                y_offset = int(self.rotation in {internal.TileRotation.LEFT, internal.TileRotation.DOWN})
                radius = size
            elif self.geometry in {internal.Geometry.CIRCLE, internal.Geometry.DOUBLE_CONCAVE}:
                x_offset = 0.5
                y_offset = 0.5
                radius = size / 2
            elif self.geometry == internal.Geometry.DOUBLE_CONVEX:
                if self.rotation == internal.TileRotation.UP:
                    x_offset = 0.5
                    y_offset = 0
                elif self.rotation == internal.TileRotation.LEFT:
                    x_offset = 0
                    y_offset = 0.5
                elif self.rotation == internal.TileRotation.DOWN:
                    x_offset = 0.5
                    y_offset = 1
                elif self.rotation == internal.TileRotation.RIGHT:
                    x_offset = 1
                    y_offset = 0.5
                else:
                    raise exceptions.ProgrammingException
                radius = size / 2
            circle_center = helpers.XYPos(x=(self.x + x_offset) * size, y=(self.y + y_offset) * size)
            self._geom_circle = tools.Disc(radius, circle_center)

            if self.geometry == internal.Geometry.CONCAVE:
                if self.rotation == internal.TileRotation.UP:
                    theta = 0
                elif self.rotation == internal.TileRotation.LEFT:
                    theta = -90
                elif self.rotation == internal.TileRotation.DOWN:
                    theta = 180
                elif self.rotation == internal.TileRotation.RIGHT:
                    theta = 90
                else:
                    raise exceptions.ProgrammingException
                self._geom_arc = tools.Arc.from_disc(self._geom_circle, theta, theta + 90)
            elif self.geometry == internal.Geometry.DOUBLE_CONCAVE:
                if self.rotation == internal.TileRotation.UP:
                    theta = 180
                elif self.rotation == internal.TileRotation.LEFT:
                    theta = 90
                elif self.rotation == internal.TileRotation.DOWN:
                    theta = 0
                elif self.rotation == internal.TileRotation.RIGHT:
                    theta = -90
                else:
                    raise exceptions.ProgrammingException
                self._geom_arc = tools.Arc.from_disc(self._geom_circle, theta, theta + 180)

        self._collision_func = self.CollisionFunctions.lookup[self.geometry]

    def _wall_geom_collide(self, entity, pos):
        entity_circle = tools.Disc(entity.radius, pos)
        return self._collision_func(self, entity_circle)


class FloorlessWall(Wall):
    """Corporeal entities cannot move horizontally through this tile.

    Note that despite the name, the wall does count as having a floor in the region that its wall occupies. It differs
    from Wall by *not* having a floor in the rest of the tile."""

    definition = 'f'
    appearance_filenames = collections.OrderedDict(
        [(internal.Geometry.RECTANGLE, 'rectangle_wall_empty.png'),
         (internal.Geometry.ANGLED, 'angled_wall_empty.png'),
         (internal.Geometry.CONCAVE, 'concave_wall_empty.png'),
         (internal.Geometry.CONVEX, 'convex_wall_empty.png'),
         (internal.Geometry.CIRCLE, 'circle_wall_empty.png'),
         (internal.Geometry.DOUBLE_CONCAVE, 'double_concave_wall_empty.png'),
         (internal.Geometry.DOUBLE_CONVEX, 'double_convex_wall_empty.png')])

    def _floor_geom_collide(self, entity, pos):
        return self._wall_geom_collide(entity, pos)


class Boundary(TileBase):
    """Represents a wall that is never passable, to any entity, ever."""

    definition = 'B'
    appearance_filenames = 'boundary.png'
    boundary = True

    
class Stair(TileBase):
    """Flightless entities can use these to move vertically upwards and downwards."""

    definition = 'X'
    appearance_filenames = collections.OrderedDict(
        [(internal.StairDirection.BOTH, 'bothstair_empty.png'),
         (internal.StairDirection.UP, 'upstair_empty.png'),
         (internal.StairDirection.DOWN, 'downstair_empty.png'),
         (internal.StairDirection.NEITHER, 'nostair_empty.png')])

    def __init__(self, **kwargs):
        super(Stair, self).__init__(**kwargs)
        self.suspend_up = self.appearance_lookup in {internal.StairDirection.BOTH, internal.StairDirection.UP}
        self.suspend_down = self.appearance_lookup in {internal.StairDirection.BOTH, internal.StairDirection.DOWN}


class FloorStair(Floor, Stair):
    """Flightless entities can use these to move vertically upwards. They block movement by corporeal entities
    downwards."""

    definition = '>'
    appearance_filenames = collections.OrderedDict(
        [(internal.StairDirection.UP, 'upstair.png'),
         (internal.StairDirection.NEITHER, 'nostair.png')])
