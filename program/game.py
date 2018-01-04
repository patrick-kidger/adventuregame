import math
import Tools as tools


import Game.config.config as config
import Game.config.internal as internal
import Game.config.strings as strings

import Game.program.misc.exceptions as exceptions
import Game.program.misc.helpers as helpers
import Game.program.misc.maps as maps
import Game.program.misc.sdl as sdl

import Game.program.entities as entities
import Game.program.tiles as tiles


class Map:
    """Holds all map data - the tiles that make up the map, plus associated information such as the map's name, its
    visual depiction on the screen, etc."""
    
    def __init__(self, background_color):
        self.screens = None  # The visual depiction of the map
        self._tile_data = None  # The tiles making up the map
        self.initialised = False  # Whether the map has been loaded yet
        self._background_color = background_color  # The background color to use where no tile is defined.
        self._max_z = -math.inf
        self._max_y = -math.inf
        self._max_x = -math.inf
        self._min_z = math.inf
        self._min_y = math.inf
        self._min_x = math.inf
        super(Map, self).__init__()

    def __iter__(self):
        """Iterates over all tiles."""
        for z_level in self._tile_data.values():
            for tile in z_level.values():
                yield tile

    def local(self, radius, pos):
        tile_radius = 2 * math.ceil(radius / tiles.diag)
        tile_center_x = math.floor(pos.x / tiles.size)
        tile_center_y = math.floor(pos.y / tiles.size)
        disc = tools.Disc(radius, pos)
        for dist in range(0, tile_radius + 1):
            for tile_x, tile_y in self._shell(tile_center_x, tile_center_y, dist):
                if disc.colliderect(sdl.Rect(tile_x * tiles.size, tile_y * tiles.size, tiles.size, tiles.size)):
                    yield self.get(tile_x, tile_y, pos.z)

    @staticmethod
    def _shell(tile_center_x, tile_center_y, dist):
        if dist == 0:
            yield tile_center_x, tile_center_y
        else:
            for i in range(0, dist):
                j = dist - i
                yield tile_center_x + i, tile_center_y + j
                yield tile_center_x - j, tile_center_y + i
                yield tile_center_x - i, tile_center_y - j
                yield tile_center_x + j, tile_center_y - i

    def get(self, item_x, item_y, item_z):
        try:
            return self._tile_data[item_z][(item_x, item_y)]
        except KeyError:
            if item_z > self._max_z or item_z < self._min_z \
                    or item_y > self._max_y or item_y < self._min_y \
                    or item_x > self._max_x or item_x < self._min_x:
                return tiles.Boundary(pos=helpers.XYZPos(x=item_x, y=item_y, z=item_z))
            else:
                return tiles.Empty(pos=helpers.XYZPos(x=item_x, y=item_y, z=item_z))

    def load_tiles(self, tile_data):
        """Loads the specified map from the given tile data."""

        self._tile_data = tile_data
        self.initialised = True
        self.screens = {}
        self._max_z = -math.inf
        self._max_y = -math.inf
        self._max_x = -math.inf
        self._min_z = math.inf
        self._min_y = math.inf
        self._min_x = math.inf
        for z, z_level in tile_data.items():
            self._max_z = max(z, self._max_z)
            self._min_z = min(z, self._min_z)
            level_max_x = -math.inf
            level_max_y = -math.inf
            level_min_x = math.inf
            level_min_y = math.inf
            for x, y in z_level.keys():
                level_max_x = max(x, level_max_x)
                level_max_y = max(y, level_max_y)
                level_min_x = min(x, level_min_x)
                level_min_y = min(y, level_min_y)
            self._max_x = max(level_max_x, self._max_x)
            self._min_x = min(level_min_x, self._min_x)
            self._max_y = max(level_max_y, self._max_y)
            self._min_y = min(level_min_y, self._min_y)
            width = level_max_x - level_min_x + 1
            height = level_max_y - level_min_y + 1
            surf = sdl.Surface((width * tiles.size, height * tiles.size))
            surf.set_offset((level_min_x * tiles.size, level_min_y * tiles.size))
            surf.fill(self._background_color)
            self.screens[z] = surf

        for tile in self:
            self.screens[tile.z].blit_offset(tile.appearance, (tile.x * tiles.size, tile.y * tiles.size))
        
    def fall(self, entity):
        """Whether or not a flightless entity will fall through the specified position.
        
        False means that they will not fall. True means that they will."""

        below_pos = helpers.XYZPos(x=entity.pos.x, y=entity.pos.y, z=entity.pos.z - 1)
        # If the entity can't fly
        if entity.flight:
            return False
        # And doesn't collide with the tile below
        if self.wall_collide(entity, below_pos):
            return False
        # And doesn't collide with the tile we're on
        if self.floor_collide(entity, entity.pos):
            return False
        # And isn't able to hold onto a suspension
        if self.suspend_collide(entity, entity.pos):
            return False
        # Then the entity falls
        return True

    def wall_collide(self, entity, pos):
        return any(tile.wall_collide(entity, pos) for tile in self.local(entity.radius, pos))

    def floor_collide(self, entity, pos):
        return any(tile.floor_collide(entity, pos) for tile in self.local(entity.radius, pos))

    def suspend_collide(self, entity, pos):
        return any(tile.suspend_collide(entity, pos) for tile in self.local(entity.radius, pos))


class Menus:
    def __init__(self, interface, clock, **kwargs):
        self.interface = interface
        self.clock = clock

        # Shortcut for convenience
        self.menu_overlay = interface.overlays.menu
        super(Menus, self).__init__(**kwargs)

    def start_menu(self, game_objects):
        menus = {internal.MenuIdentifiers.MAIN_MENU: self._main_menu,
                 internal.MenuIdentifiers.MAP_SELECT: self._map_select,
                 internal.MenuIdentifiers.OPTIONS: self._options}
        game_start_menu = {internal.MenuIdentifiers.GAME_START}
        self._menu(menus, game_start_menu, game_objects)

    def _menu(self, menus, finish_menus, game_objects):
        """Displays the menu system"""
        old_menu = None
        current_menu = internal.MenuIdentifiers.MAIN_MENU  # The first menu displayed
        self.clock.tick()
        with self.interface.use('menu'):
            while True:  # Wait for the user to navigate through the menu system
                if old_menu != current_menu:
                    old_menu = current_menu
                    self.interface.reset('menu')
                    menus[current_menu](game_objects)  # Set up the current menu
                    self.interface.flush()
                while True:  # Wait for input from this menu
                    self.clock.tick(config.RENDER_FRAMERATE)
                    inputs = self.interface.inp()
                    self.interface.flush()
                    if inputs:
                        if len([c_m for c_m, input_type in inputs if input_type != internal.InputTypes.MENU]):
                            # If we have any non-MENU inputs
                            raise exceptions.ProgrammingException
                        current_menu = next(c_m for c_m, input_type in inputs if input_type == internal.InputTypes.MENU)
                        break
                if current_menu in finish_menus:
                    break

    def _main_menu(self, game_objects):
        """Displays the main menu"""
        map_select_button = self.menu_overlay.submit(strings.MainMenu.START,
                                                     horz_alignment=internal.Alignment.CENTER,
                                                     vert_alignment=internal.Alignment.CENTER)
        map_select_button.on_submit(lambda menu_results, pos:
                                    (internal.MenuIdentifiers.MAP_SELECT, False))

        options_button = self.menu_overlay.submit(strings.MainMenu.OPTIONS,
                                                  horz_alignment=internal.Alignment.CENTER,
                                                  vert_alignment=internal.Alignment.BOTTOM)
        options_button.on_submit(lambda menu_results, pos:
                                 (internal.MenuIdentifiers.OPTIONS, False))

        close_button = self.menu_overlay.button(strings.EscapeMenu.CLOSE,
                                                horz_alignment=internal.Alignment.RIGHT,
                                                vert_alignment=internal.Alignment.BOTTOM)
        def close(menu_results, pos):
            raise exceptions.CloseException
        close_button.on_mouseup(close)

    def _map_select(self, game_objects):
        """Displays the menu to select a map."""
        map_names = maps.map_names()

        menu_list = self.menu_overlay.list(title=strings.MapSelectMenu.TITLE, entry_text=map_names, necessary=True)

        game_start_button = self.menu_overlay.submit(strings.MapSelectMenu.SELECT_MAP)
        def game_start_button_press(menu_results, pos):
            menu_to_go_to = internal.MenuIdentifiers.GAME_START
            selected_index = menu_results[menu_list]
            map_name = map_names[selected_index]
            try:
                map_name, tile_data, start_pos = maps.get_map_data_from_map_name(map_name, tiles.all_tiles())
            except exceptions.MapLoadException:
                bad_map_message = self.menu_overlay.messagebox(strings.FileLoading.BAD_LOAD_TITLE,
                                                               strings.FileLoading.BAD_LOAD_MESSAGE,
                                                               select=True)
                close_messagebox = lambda *args, **kwargs: (self.menu_overlay.remove(bad_map_message), False)
                bad_map_message.on_mouseup_button(strings.Menus.OK, close_messagebox)
                bad_map_message.on_un_mousedown(close_messagebox)
                self.menu_overlay.screen.update_cutouts()
                self.interface.flush()
                menu_to_go_to = internal.MenuIdentifiers.MAP_SELECT
            else:
                game_objects.map.load_tiles(tile_data)
                # + 0.5 to move the player to center of the tile
                game_objects.player.pos = helpers.XYZPos(x=(start_pos.x + 0.5) * tiles.size,
                                                         y=(start_pos.y + 0.5) * tiles.size,
                                                         z=start_pos.z)
            return menu_to_go_to, False
        game_start_button.on_submit(game_start_button_press)

        main_menu_button = self.menu_overlay.back(strings.MapSelectMenu.MAIN_MENU)
        main_menu_button.on_back(lambda menu_results, pos:
                                 (internal.MenuIdentifiers.MAIN_MENU, False))

    def _options(self, game_objects):
        main_menu_button = self.menu_overlay.back(strings.MapSelectMenu.MAIN_MENU)
        main_menu_button.on_back(lambda menu_results, pos:
                                 (internal.MenuIdentifiers.MAIN_MENU, False))


class Simulation:
    def __init__(self, game_objects, interface, clock, **kwargs):
        self.game_objects = game_objects
        self.interface = interface
        self.clock = clock

        self._abs_move_command = None
        self._camera_offset = None
        super(Simulation, self).__init__(**kwargs)

    def reset(self):
        self._abs_move_command = None
        self._camera_offset = tools.Object(x=0, y=0)

    def run(self):
        """The main game loop."""
        with self.interface.use('game'):
            accumulator = 0
            physics_framelength = 1000 / config.PHYSICS_FRAMERATE
            self.clock.tick(config.RENDER_FRAMERATE)
            self._render()
            while True:
                while accumulator >= 0:
                    inputs = self.interface.inp()
                    self._tick(inputs)
                    accumulator -= physics_framelength
                accumulator += self.clock.tick(config.RENDER_FRAMERATE)
                self._render()

    def _tick(self, inputs):
        """A single tick of the game."""
        # We should only handle falling once per tick
        if self.game_objects.map.fall(self.game_objects.player):
            self._abs_move_command = None
            self.game_objects.player.fall_counter += 1
            if self.game_objects.player.fall_counter == self.game_objects.player.fall_speed:
                self._move_entity_vert(internal.Action.VERTICAL_DOWN, self.game_objects.player)
                self.game_objects.player.fall_counter = 0

        for play_inp, input_type in inputs:
            # But the result of some inputs might put us in a falling position, in which case we shouldn't evaluate the
            # other inputs
            if not self.game_objects.map.fall(self.game_objects.player):
                if input_type == internal.InputTypes.MOVE_ABS:
                    # play_inp is relative to the camera, so here we convert it to absolute coordinates.
                    self._abs_move_command = helpers.XYPos(x=play_inp.x + self._camera_topleft.x,
                                                           y=play_inp.y + self._camera_topleft.y)
                elif input_type == internal.InputTypes.ACTION:
                    self._abs_move_command = None
                    self._action_entity(play_inp, self.game_objects.player)
                elif input_type == internal.InputTypes.MOVE_CAMERA:
                    self._move_camera(play_inp)
                else:
                    raise exceptions.ProgrammingException

        if self._abs_move_command is not None:
            self._move_entity_abs(self._abs_move_command, self.game_objects.player)

    def _render(self):
        """Outputs the current game state."""
        self.interface.reset('game')
        self.interface.out('game', self.game_objects.map.screens[self.game_objects.player.z],
                           offset=self._camera_topleft)
        self.interface.out('game', self.game_objects.player.appearance, (self.game_objects.player.topleft_x,
                                                                         self.game_objects.player.topleft_y),
                           offset=self._camera_topleft)
        self.interface.flush()

    @property
    def _camera_topleft(self):
        x = self.game_objects.player.x + self._camera_offset.x - self.interface.screen_size.width / 2
        y = self.game_objects.player.y + self._camera_offset.y - self.interface.screen_size.height / 2
        return helpers.XYPos(x=x, y=y)

    def _move_camera_offset(self, x, y):
        self._camera_offset.x = tools.clamp(self._camera_offset.x + x, -1 * config.MAX_CAMERA_OFFSET,
                                            config.MAX_CAMERA_OFFSET)
        self._camera_offset.y = tools.clamp(self._camera_offset.y + y, -1 * config.MAX_CAMERA_OFFSET,
                                            config.MAX_CAMERA_OFFSET)

    def _move_camera(self, pos):
        dir_x = pos.x - self.interface.screen_size.width / 2
        dir_y = pos.y - self.interface.screen_size.height / 2
        scaling = config.CAMERA_SPEED / math.sqrt(dir_x ** 2 + dir_y ** 2)
        x = dir_x * scaling
        y = dir_y * scaling
        self._move_camera_offset(x, y)

    def _action_entity(self, action, entity):
        vert_actions = {internal.Action.VERTICAL_UP, internal.Action.VERTICAL_DOWN}
        horz_actions = {internal.Move.LEFT, internal.Move.RIGHT, internal.Move.UP, internal.Move.DOWN}
        if action in vert_actions:
            self._move_entity_vert(action, entity)
        elif action in horz_actions:
            self._move_entity_rel(action, entity)
        else:
            raise exceptions.ProgrammingException

    def _move_entity_vert(self, action, entity):
        vert_actions = {internal.Action.VERTICAL_UP: 1,
                        internal.Action.VERTICAL_DOWN: -1}
        direction = vert_actions[action]
        new_entity_pos = helpers.XYZPos(x=entity.x, y=entity.y, z=entity.z + direction)
        if direction == 1:
            if self.game_objects.map.wall_collide(entity, new_entity_pos) or \
                    self.game_objects.map.floor_collide(entity, new_entity_pos):
                return
        if direction == -1:
            if self.game_objects.map.wall_collide(entity, new_entity_pos) or \
                    self.game_objects.map.floor_collide(entity, entity.pos):
                return
        entity.z += direction

    def _move_entity_rel(self, action, entity):
        horz_actions = {internal.Move.LEFT: helpers.XYPos(x=-1, y=0),
                        internal.Move.RIGHT: helpers.XYPos(x=1, y=0),
                        internal.Move.UP: helpers.XYPos(x=0, y=-1),
                        internal.Move.DOWN: helpers.XYPos(x=0, y=1)}
        direction = horz_actions[action]
        self._move_entity(direction, entity)

    def _move_entity_abs(self, pos, entity):
        direction = helpers.XYPos(x=pos.x - entity.x, y=pos.y - entity.y)
        if direction.x ** 2 + direction.y ** 2 < internal.move_tolerance:
            self._abs_move_command = None
        else:
            self._move_entity(direction, entity)

    def _move_entity(self, direction, entity):
        scaling = entity.speed / math.sqrt(direction.x ** 2 + direction.y ** 2)
        move_x = direction.x * scaling
        move_y = direction.y * scaling
        new_entity_pos = helpers.XYZPos(x=entity.x + move_x, y=entity.y + move_y, z=entity.z)
        if self.game_objects.map.wall_collide(entity, new_entity_pos):
            self._abs_move_command = None
        else:
            entity.x = new_entity_pos.x
            entity.y = new_entity_pos.y

            if entity is self.game_objects.player:
                self._move_camera_offset(-1 * move_x, -1 * move_y)


class GameObjects:
    def __init__(self, map_background_color):
        self.map = None
        self.player = None
        self._map_background_color = map_background_color

    def reset(self):
        self.map = Map(self._map_background_color)
        self.player = entities.Player()


class GameRunner:
    """Main game instance."""

    def __init__(self, menus, simulation, interface, game_objects, **kwargs):
        self.menus = menus
        self.simulation = simulation
        self.interface = interface
        self.game_objects = game_objects

        super(GameRunner, self).__init__(**kwargs)

    def reset(self):
        """Resets the game. (But does not start a new one.)"""
        self.interface.reset()
        self.game_objects.reset()
        self.simulation.reset()

    def start(self):
        """Starts the game."""
        while True:
            try:
                self.reset()
                self.menus.start_menu(self.game_objects)
                self.simulation.run()
                break
            except exceptions.CloseException:
                sdl.quit()
                break
            except exceptions.QuitException:
                pass
