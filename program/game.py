import collections
import math
import Tools as tools


import Game.config.config as config
import Game.config.internal_strings as internal_strings
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl
import Game.program.entities as entities
import Game.program.tiles as tiles

    
class Map:
    """Holds all map data - the tiles that make up the map, plus associated information such as the map's name, its
    visual depiction on the screen, etc."""
    
    def __init__(self, background_color):
        self.name = None  # The name of the map (surprise!)
        self.tile_data = None  # The tiles making up the map
        self.screens = None  # The visual depiction of the map
        self.background_color = background_color  # The background color to use where no tile is defined.
        super(Map, self).__init__()

    def __getitem__(self, item):
        try:
            return self.tile_data[item.z][item.y][item.x]
        except IndexError:
            return tiles.Boundary(pos=tools.Object(x=item.x, y=item.y, z=item.z))

    def __iter__(self):
        """Iterates over all tiles."""
        for z_level in self.tile_data:
            for y_row in z_level:
                for tile in y_row:
                    yield tile

    def local(self, radius, center, z_level):
        tile_radius = math.ceil(radius / tiles.size)
        tile_center = tools.Object(x=math.floor(center.x / tiles.size), y=math.floor(center.y / tiles.size))
        for x in range(tile_center.x - tile_radius, tile_center.x + tile_radius + 1):
            for y in range(tile_center.y - tile_radius, tile_center.y + tile_radius + 1):
                yield self[tools.Object(x=x, y=y, z=z_level)]

    def load(self, map_data):
        """Loads the specified map."""
        self.name = map_data.name

        self.tile_data = tools.nonneg_list()
        areas = []
        for z, data_z_level in enumerate(map_data.tile_data):
            self.tile_data.append(tools.nonneg_list())
            max_x = 0
            for y, data_y_row in enumerate(data_z_level):
                self.tile_data[z].append(tools.nonneg_list())
                for x, single_tile_data in enumerate(data_y_row):
                    tile = tiles.Tile(pos=tools.Object(z=z, y=y, x=x))
                    tile.set_from_data(single_tile_data)
                    self.tile_data[z][y].append(tile)
                max_x = max(max_x, x)
            areas.append(tools.Object(x=max_x + 1, y=y + 1))
        self.convert_walls()

        self.screens = [sdl.Surface((area.x * tiles.size, area.y * tiles.size)) for area in areas]
        for screen in self.screens:
            screen.fill(self.background_color)
        for tile in self:
            self.screens[tile.z].blit(tile.appearance, (tile.x * tiles.size, tile.y * tiles.size))

    def convert_walls(self):
        """Customises the visuals of all the walls based on adjacent walls."""
        adj_directions = (internal_strings.WallAdjacency.DOWN, internal_strings.WallAdjacency.UP,
                          internal_strings.WallAdjacency.RIGHT, internal_strings.WallAdjacency.LEFT)
        for tile in self:
            if tile.wall:
                adj_objs = (tools.Object(x=tile.x + j, y=tile.y + i, z=tile.z)
                            for i, j in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                adj_tiles = (self[adj_obj] for adj_obj in adj_objs)
                for adj_tile, adj_direction in zip(adj_tiles, adj_directions):
                    if adj_tile.wall:
                        adj_tile.adjacent_walls.add(adj_direction)

        for tile in self:
            if tile.wall:
                tile.convert_wall()
        
    def fall(self, pos):
        """Whether or not a flightless entity will fall through the specified position.
        
        False means that they will not fall. True means that they will."""
        this_tile = self[pos]
        if this_tile.suspend:
            return False
        pos_beneath = tools.Object(x=pos.x, y=pos.y, z=pos.z - 1)
        return not(self[pos_beneath].ceiling or this_tile.floor)

    
class MainGame:
    """Main game instance."""

    def __init__(self, maps_access, interface):
        self.clock = sdl.time.Clock()
        self._maps_access = maps_access  # Access to all the saved maps
        self.out = interface.out  # Output to screen
        self.inp = interface.inp  # Receive input from user
        interface.register_game(self)

        # Immediately redefined in reset()
        # Just defined here for clarity about what instance properties we have
        self.map = None  # The map that the player is on
        self.player = None  # The player. Unsurprisingly.
        self.debug_mode = None  # Whether or not cheaty debug commands can be executed
        
    def reset(self):
        """Resets the game. (But does not start a new one.)"""
        self.map = Map(self.out.overlays.game.background_color)
        self.player = entities.Player()

        # Must reset output before input, as input might wish to feed something to the output as part of its reset.
        # (e.g. the prompt in the debug console)
        self.out.reset()
        self.inp.reset()

        self.debug_mode = False
        
    def start(self):
        """Starts the game."""
        reset = True
        menu = True
        while True:
            try:
                if reset:
                    self.reset()
                    reset = False
                if menu:
                    self._menu()
                    menu = False
                self._run()
                break
            except exceptions.CloseException:
                sdl.quit()
                break
            except exceptions.BaseQuitException as e:
                if isinstance(e, exceptions.QuitException):
                    menu = True
                if isinstance(e, exceptions.ResetException):
                    reset = True

    def _menu(self):
        """Displays the menu system"""
        current_menu = internal_strings.Menus.MAIN_MENU  # The first menu displayed
        menus = {internal_strings.Menus.MAIN_MENU: self._main_menu,  # All of the menus
                 internal_strings.Menus.MAP_SELECT: self._map_select,
                 internal_strings.Menus.OPTIONS: self._options}
        self.clock.tick()
        with self._use_interface('menu'):
            while True:  # Wait for the user to navigate through the menu system
                self.out.overlays.menu.reset()
                callback = menus[current_menu]()  # Set up the current menu
                self.out.flush()
                got_input = True
                while got_input:  # Wait for input from this menu
                    self.clock.tick(config.RENDER_FRAMERATE)
                    inputs = self.inp()
                    self.out.flush()
                    for menu_results, input_type in inputs:
                        if input_type == internal_strings.InputTypes.MENU:  # Once a submit element is activated
                            current_menu = callback(menu_results)  # Do whatever this menu does
                            got_input = False
                            break
                if current_menu == internal_strings.Menus.GAME_START:
                    # Start the game
                    break

    def _main_menu(self):
        """Displays the main menu"""
        map_select_button = self.out.overlays.menu.submit(strings.MainMenu.START,
                                                          horz_alignment=internal_strings.Alignment.CENTER,
                                                          vert_alignment=internal_strings.Alignment.CENTER)

        options_button = self.out.overlays.menu.submit(strings.MainMenu.OPTIONS,
                                                       horz_alignment=internal_strings.Alignment.CENTER,
                                                       vert_alignment=internal_strings.Alignment.BOTTOM)

        def callback(menu_results):
            button_menu_map = {map_select_button: internal_strings.Menus.MAP_SELECT,
                               options_button: internal_strings.Menus.OPTIONS}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            return menu_to_go_to

        return callback

    def _map_select(self):
        """Displays the menu to select a map."""
        map_names = self._maps_access.setup_and_find_map_names()

        menu_list = self.out.overlays.menu.list(title=strings.MapSelectMenu.TITLE, entry_text=map_names, necessary=True)
        game_start_button = self.out.overlays.menu.submit(strings.MapSelectMenu.SELECT_MAP)
        main_menu_button = self.out.overlays.menu.back(strings.MapSelectMenu.MAIN_MENU)

        def callback(menu_results):
            button_menu_map = {game_start_button: internal_strings.Menus.GAME_START,
                               main_menu_button: internal_strings.Menus.MAIN_MENU}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            if pressed_button is game_start_button:
                selected_index = menu_results[menu_list]
                map_name = map_names[selected_index]
                map_ = self._maps_access.get_map(map_name)

                self.map.load(map_)
                self.player.x = map_.start_pos.x * tiles.size
                self.player.y = map_.start_pos.y * tiles.size
                self.player.z = map_.start_pos.z

            return menu_to_go_to

        return callback

    def _options(self):
        main_menu_button = self.out.overlays.menu.back(strings.MapSelectMenu.MAIN_MENU)

        def callback(menu_results):
            button_menu_map = {main_menu_button: internal_strings.Menus.MAIN_MENU}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            return menu_to_go_to

        return callback

    @staticmethod
    def _standard_menu_movement(menu_results, button_menu_map):
        pressed_buttons = [key for key in button_menu_map.keys() if menu_results[key]]
        if len(pressed_buttons) != 1:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.MENU_MOVE_WRONG)
        pressed_button = pressed_buttons[0]

        menu_to_go_to = button_menu_map[pressed_button]
        if menu_to_go_to is None:
            raise exceptions.ProgrammingException(internal_strings.Exceptions.MENU_MOVE_WRONG)

        return pressed_button, menu_to_go_to

    def _run(self):
        """The main game loop."""
        with self._use_interface('game'):
            accumulator = 0
            physics_framelength = 1000 / config.PHYSICS_FRAMERATE
            self.clock.tick(config.RENDER_FRAMERATE)
            self.render()
            while True:
                while accumulator >= 0:
                    inputs = self.inp()
                    self._tick(inputs)
                    accumulator -= physics_framelength
                accumulator += self.clock.tick(config.RENDER_FRAMERATE)
                self.render()

    def _use_interface(self, interface_name):
        """For use in 'with' statements. Enables both the listener and the overlay with the name :interface_name:"""
        return self.out.use(interface_name) + self.inp.use(interface_name)
    
    def _tick(self, inputs):
        """A single tick of the game."""
        use_player_input = True
        if not self.player.flight and self.map.fall(self.player.square_pos):
            use_player_input = False
            self.player.fall_counter += 1
            if self.player.fall_counter == self.player.fall_speed:
                self._move_entity_vert(internal_strings.Action.VERTICAL_DOWN, self.player)
                self.player.fall_counter = 0

        if use_player_input:
            for play_inp, input_type in inputs:
                if input_type == internal_strings.InputTypes.ACTION:
                    self._action_entity(play_inp, self.player)
                elif input_type == internal_strings.InputTypes.NO_INPUT:
                    pass
                else:
                    raise exceptions.ProgrammingException(internal_strings.Exceptions.INVALID_INPUT_TYPE.format(input=input_type))

    def render(self):
        """Outputs the current game state."""
        self.out.overlays.game.reset()
        self.out.overlays.game(self.map.screens[self.player.z])
        self.out.overlays.game(self.player.appearance, (self.player.x, self.player.y))
        self.out.flush()

    def _action_entity(self, action, entity):
        vert_actions = (internal_strings.Action.VERTICAL_UP, internal_strings.Action.VERTICAL_DOWN)
        horz_actions = {internal_strings.Move.LEFT: tools.Object(x=-1, y=0),
                        internal_strings.Move.RIGHT: tools.Object(x=1, y=0),
                        internal_strings.Move.UP: tools.Object(x=0, y=-1),
                        internal_strings.Move.DOWN: tools.Object(x=0, y=1)}
        if action in vert_actions:
            self._move_entity_vert(action, entity)
            return
        try:
            direction = horz_actions[action]
        except KeyError:
            pass
        else:
            self._move_entity_rel(direction, entity)

    def _move_entity_vert(self, action, entity):
        current_pos = entity.square_pos
        old_tile = self.map[current_pos]
        if action == internal_strings.Action.VERTICAL_UP:
            dir = 1
        else:  # Move down
            dir = -1

        new_pos = tools.Object(x=current_pos.x, y=current_pos.y, z=current_pos.z + dir)
        new_tile = self.map[new_pos]

        if new_tile.boundary:
            return  # Nothing can move through boundaries

        if action == internal_strings.Action.VERTICAL_UP:
            if (old_tile.ceiling or new_tile.floor) and not entity.incorporeal:
                return  # Corporeal entities cannot pass through solid floors and ceilings.
            if not((old_tile.suspend and new_tile.suspend) or entity.flight):
                return  # Flightless entities require a suspension to move vertically upwards

        else:  # Move down
            if (old_tile.floor or new_tile.ceiling) and not entity.incorporeal:
                return  # Corporeal entities cannot pass through solid floors and ceilings.

        entity.z += dir

    def _move_entity_rel(self, direction, entity):
        scaling = entity.speed / math.sqrt(direction.x ** 2 + direction.y ** 2)
        new_entity_pos = tools.Object(x=entity.center_x + direction.x * scaling,
                                      y=entity.center_y + direction.y * scaling)
        for tile in self.map.local(entity.radius, new_entity_pos, entity.z):
            if tile.boundary or (tile.solid and not entity.incorporeal):
                if tools.Circle(entity.radius, new_entity_pos)\
                        .colliderect(sdl.Rect(tile.x * tiles.size, tile.y * tiles.size, tiles.size, tiles.size)):
                    break
        else:
            entity.center_x = new_entity_pos.x
            entity.center_y = new_entity_pos.y

    def _move_entity_abs(self, pos, entity):
        direction = tools.Object(x=pos.x - entity.x, y=pos.y - entity.y)
        self._move_entity_rel(direction, entity)
