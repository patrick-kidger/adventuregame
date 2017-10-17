import copy
import time

import Tools as tools

import Maze.config.config as config
import Maze.config.strings as strings
import Maze.program.misc.exceptions as exceptions
import Maze.program.misc.sdl as sdl
import Maze.program.entities as entities
import Maze.program.tiles as tiles


class TileData(object):
    """Holds all the Tiles."""
    def __init__(self):
        self._tile_data = None
        self.areas = None
        
    def __getitem__(self, item):
        return self._tile_data[item.z, item.y, item.x]

    def __iter__(self):
        for z, z_level in enumerate(self._tile_data):
            for y, y_row in enumerate(z_level):
                for x, tile in enumerate(y_row):
                    yield tools.Object(x=x, y=y, z=z, tile=tile, y_row=y_row, z_level=z_level)
        
    def load(self, tile_data):
        """Sets the tile data from the loaded tile data."""
        self._tile_data = tools.qlist()
        self.areas = []
        for z, data_z_level in enumerate(tile_data):
            self._tile_data.append(tools.qlist())
            max_x = 0
            for y, data_y_row in enumerate(data_z_level):
                self._tile_data[z].append(tools.qlist())
                for x, single_tile_data in enumerate(data_y_row):
                    tile = tiles.Tile(pos=tools.Object(z=z, y=y, x=x))
                    tile.set_from_data(single_tile_data)
                    self._tile_data[z][y].append(tile)
                max_x = max(max_x, x)
            self.areas.append(tools.Object(x=max_x, y=y))
        self.convert_walls()
                        
    def convert_walls(self):
        """Customises the visuals of all the walls based on adjacent walls."""
        for tile_data in self:
            if tile_data.tile.wall:
                adj_tiles = (tile_data.z_level[tile_data.y + i][tile_data.x + j]
                             for i, j in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                adj_directions = (config.WallAdjacency.DOWN, config.WallAdjacency.UP,
                                  config.WallAdjacency.RIGHT, config.WallAdjacency.LEFT)
                for adj_tile, adj_direction in zip(adj_tiles, adj_directions):
                    if adj_tile.wall:
                        adj_tile.adjacent_walls.add(adj_direction)

        for tile_data in self:
            if tile_data.tile.wall:
                tile_data.tile.convert_wall()
                        
    def level(self, z_level):
        """Gets a z level slice of the tile data."""
        return self._tile_data[z_level]
        
    
class Map(object):
    """Holds all map data."""
    
    def __init__(self):
        self.name = None
        self.tile_data = TileData()
        self.screens = None

    def load(self, map_data):
        """Loads the specified map."""
        self.name = map_data.name
        self.tile_data.load(map_data.tile_data)
        self.screens = [sdl.Surface(((area.x + 1) * config.TILE_X, (area.y + 1) * config.TILE_Y))
                        for area in self.tile_data.areas]
        for tile_data in self.tile_data:
            self.screens[tile_data.z].blit(tile_data.tile.appearance,
                                           (tile_data.x * config.TILE_X, tile_data.y * config.TILE_Y))
                    
    def level(self, z_level):
        """Gets a specified z-level of the map."""
        return self.tile_data.level(z_level)

    @staticmethod
    def rel(pos, direction):
        """Gets a position based on an existing position and a direction."""
        new_pos = copy.deepcopy(pos)
        if direction == config.Play.UP:
            new_pos.y -= 1
        elif direction == config.Play.DOWN:
            new_pos.y += 1
        elif direction == config.Play.LEFT:
            new_pos.x -= 1
        elif direction == config.Play.RIGHT:
            new_pos.x += 1
        elif direction == config.Play.VERTICAL_UP:
            new_pos.z += 1
        elif direction == config.Play.VERTICAL_DOWN:
            new_pos.z -= 1
        else:
            raise exceptions.ProgrammingException(strings.Play.Exceptions.UNEXPECTED_DIRECTION.format(direction=direction))
        return new_pos
        
    def fall(self, pos):
        """Whether or not a flightless entity will fall through the specified position.
        
        False means that they will not fall. True means that they will."""
        this_tile = self.tile_data[pos]
        if this_tile.suspend:
            return False
        pos_beneath = self.rel(pos, config.Play.VERTICAL_DOWN)
        return not(self.tile_data[pos_beneath].ceiling or this_tile.floor)

    
class MazeGame(object):
    """Main game."""
    def __init__(self, maps_access, interface):
        self.maps_access = maps_access
        self.out = interface.output
        self.inp = interface.input

        self.map = None     # Immediately redefined in reset()
        self.player = None  # Just defined here for clarity about what instance properties we have
        self.debug = None   #
        self.reset()
        
    def reset(self):
        """Resets the game. (But does not start a new one.)"""
        self.map = Map()
        self.player = entities.Player()

        self.debug = False
        
    def start(self):
        """Starts the game."""
        self.map_select()
        return self._run()
        
    def map_select(self):
        """Gives the menu to select a map."""
        # Map Selection
        map_names = self.maps_access.setup_and_find_map_names()
        # Print the map options
        numbers = [strings.MapSelect.option_number.format(number=i) for i in range(len(map_names))]

        debug_enabled = self.out.overlays.debug.enabled
        self.out.overlays.debug.enabled = True
        self.out.overlays.debug.clear()
        self.out.overlays.debug.table(title=strings.MapSelect.title, columns=[numbers, map_names],
                                      headers=strings.MapSelect.headers)
        self.out.overlays.debug(strings.MapSelect.input)
        self.out.flush()
        # Get the selected map option
        while True:
            try:
                inp = self.inp.debug_inp(num_chars=2, type_arg=int)
                self.out.overlays.debug('\n')
                self.out.flush()
                map_name = map_names[inp]
            except (ValueError, IndexError):  # Cannot cast to int or number does not correspond to a map
                self.inp.invalid_input()
            else:
                map_ = self.maps_access.get_map(map_name)
                break

        self.out.overlays.debug.enabled = debug_enabled
        self.out.overlays.debug.clear()

        # Map
        self.map.load(map_)
        
        # Player
        self.player.set_pos(map_.start_pos)

    def _run(self):
        """The main game loop."""
        completed = False  # Game has not yet finished
        # Information to be carried over to the next tick, if we don't allow input in this one.
        skip = tools.Object(skip=False)
        self.render()
        while not completed:
            tick_result = self._tick(skip)
            completed = tick_result.completed
            skip = tick_result.skip
            if tick_result.render:
                self.render()
        return tick_result.again
    
    def _tick(self, skip):
        """A single tick of the game."""
        if skip.skip:
            time.sleep(config.SLEEP_SKIP)
            play_inp, is_move = skip.play_inp, skip.is_move
        else:
            play_inp, is_move = self.inp()

        if is_move:
            move_result = self.move_entity(play_inp, self.player)
            if skip.skip and not move_result:
                raise exceptions.ProgrammingException(strings.Play.Exceptions.INVALID_FORCE_MOVE)
            input_result = tools.Object(completed=False, render=True, progress=True, again=False)
            if not self.player.flight and self.map.fall(self.player.pos):
                input_result.skip = tools.Object(skip=True, play_inp=config.Play.VERTICAL_DOWN, is_move=True)
            else:
                input_result.skip = tools.Object(skip=False)
        else:
            input_result = play_inp(self)

        if input_result.progress:
            # Do stuff
            pass
        return input_result

    def render(self):
        """Outputs the current game state."""
        self.out.overlays.game.clear()
        self.out.overlays.game.screen.blit(self.map.screens[self.player.z], (0, 0))
        self.out.overlays.game.screen.blit(self.player.appearance,
                                           (self.player.x * config.TILE_X, self.player.y * config.TILE_Y))
        self.out.flush()
            
    def move_entity(self, direction, entity):
        """Moves the entity in the specified direction.
        
        Returns True/False based on if it was successfully able to move it or not."""
        current_pos = entity.pos
        new_pos = self.map.rel(current_pos, direction)
        old_tile = self.map.tile_data[current_pos]
        new_tile = self.map.tile_data[new_pos]
        
        if isinstance(new_tile, tools.qlist.Eater):
            return False  # If we're trying to move outside the edge of the map
        if new_tile.boundary:
            return False  # Nothing can pass through boundaries
        if new_tile.solid and not entity.incorporeal:
            return False  # Corporeal entities cannot pass through solid barriers
        if direction == config.Play.VERTICAL_UP:
            if (old_tile.ceiling or new_tile.floor) and not entity.incorporeal:
                return False  # Corporeal entities cannot pass through solid floors and ceilings.
            if not((old_tile.suspend and new_tile.suspend) or entity.flight):
                return False  # Flightless entities require a asuspension to move vertically upwards
        if direction == config.Play.VERTICAL_DOWN:
            if (old_tile.floor or new_tile.ceiling) and not entity.incorporeal:
                return False  # Corporeal entities cannot pass through solid floors and ceilings.
        entity.set_pos(new_pos)
        return True
