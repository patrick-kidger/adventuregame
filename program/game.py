import math
import Tools as tools


import Game.config.config as config
import Game.config.internal as internal
import Game.config.strings as strings

import Game.data.maps as maps

import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl
import Game.program.entities as entities
import Game.program.tiles as tiles

    
class Map:
    """Holds all map data - the tiles that make up the map, plus associated information such as the map's name, its
    visual depiction on the screen, etc."""
    
    def __init__(self, background_color):
        self.tile_data = None  # The tiles making up the map
        self.screens = None  # The visual depiction of the map
        self.background_color = background_color  # The background color to use where no tile is defined.
        super(Map, self).__init__()

    def __getitem__(self, item):
        try:
            return self.tile_data[item.z][(item.x, item.y)]
        except KeyError:
            return tiles.Boundary(pos=tools.Object(x=item.x, y=item.y, z=item.z))

    def __iter__(self):
        """Iterates over all tiles."""

        for z_level in self.tile_data.values():
            for tile in z_level.values():
                yield tile

    def local(self, radius, pos):
        tile_radius = math.ceil(radius / tiles.size)
        tile_center = tools.Object(x=math.floor(pos.x / tiles.size), y=math.floor(pos.y / tiles.size))
        for x in range(tile_center.x - tile_radius, tile_center.x + tile_radius + 1):
            for y in range(tile_center.y - tile_radius, tile_center.y + tile_radius + 1):
                yield self[tools.Object(x=x, y=y, z=pos.z)]

    def load_tiles(self, tile_data):
        """Loads the specified map from the given tile data."""

        self.tile_data = tile_data
        areas = []
        for z_level in tile_data.values():
            max_x = -math.inf
            max_y = -math.inf
            min_x = math.inf
            min_y = math.inf
            for x, y in z_level.keys():
                max_x = max(x, max_x)
                max_y = max(y, max_y)
                min_x = min(x, min_x)
                min_y = min(y, min_y)
            areas.append(tools.Object(x=max_x - min_x + 1, y=max_y - min_y + 1, min_x=min_x, min_y=min_y))

        self.screens = []
        for area in areas:
            surf = sdl.Surface((area.x * tiles.size, area.y * tiles.size))
            surf.set_offset((area.min_x * tiles.size, area.min_y * tiles.size))
            surf.fill(self.background_color)
            self.screens.append(surf)

        for tile in self:
            self.screens[tile.z].blit_offset(tile.appearance, (tile.x * tiles.size, tile.y * tiles.size))
        
    def fall(self, entity):
        """Whether or not a flightless entity will fall through the specified position.
        
        False means that they will not fall. True means that they will."""

        below_pos = tools.Object(x=entity.pos.x, y=entity.pos.y, z=entity.pos.z - 1)
        # If the entity can't fly
        if entity.flight:
            return False
        # And doesn't collide with the tile below
        if self.entity_wall_collide(entity, below_pos):
            return False
        # And doesn't collide with the tile we're on
        if self.entity_floor_collide(entity, entity.pos):
            return False
        # And isn't able to hold onto a suspension
        if self.entity_suspend_collide(entity, entity.pos):
            return False
        # Then the entity falls
        return True

    def entity_wall_collide(self, entity, pos):
        for tile in self.local(entity.radius, pos):
            # If the tile has a wall to collide with
            if tile.boundary or (tile.solid and not entity.incorporeal):
                # And the entity collides with the square that is the tile
                if self._collide_square(entity, pos, tile):
                    # Then the entity collides with the wall
                    return True
        return False

    def entity_floor_collide(self, entity, pos):
        for tile in self.local(entity.radius, pos):
            # If the tile has a floor to collide with
            if tile.floor and not entity.incorporeal:
                # And the entity collides with the square that is the tile
                if self._collide_square(entity, pos, tile):
                    # Then the entity collides with the floor
                    return True
        return False

    def entity_suspend_collide(self, entity, pos):
        for tile in self.local(entity.radius, pos):
            # If the tile has a suspension to collide with
            if tile.suspend_up or tile.suspend_down:
                # And the entity collides with the square that is the tile
                if self._collide_square(entity, pos, tile):
                    # Then the entity collides with the suspension
                    return True
            # A bit special: incorporeal entities shouldn't just fall through the floor to the bottom of the world, so
            # we let them count floors as suspensions.
            if tile.floor and entity.incorporeal:
                if self._collide_square(entity, pos, tile):
                    return True
        return False

    @staticmethod
    def _collide_square(entity, pos, tile):
        """Whether or not the given entity at the given position collides with the square that is the tile."""
        return tools.Circle(entity.radius, pos).colliderect(sdl.Rect(tile.x * tiles.size,
                                                                     tile.y * tiles.size,
                                                                     tiles.size,
                                                                     tiles.size))


class MainGame:
    """Main game instance."""

    def __init__(self, interface):
        self.clock = sdl.time.Clock()
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
        current_menu = internal.MenuIdentifiers.MAIN_MENU  # The first menu displayed
        menus = {internal.MenuIdentifiers.MAIN_MENU: self._main_menu,  # All of the menus
                 internal.MenuIdentifiers.MAP_SELECT: self._map_select,
                 internal.MenuIdentifiers.OPTIONS: self._options}
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
                        if input_type == internal.InputTypes.MENU:  # Once a submit element is activated
                            current_menu = callback(menu_results)  # Do whatever this menu does
                            got_input = False
                            break
                if current_menu == internal.MenuIdentifiers.GAME_START:
                    # Start the game
                    break

    def _main_menu(self):
        """Displays the main menu"""
        map_select_button = self.out.overlays.menu.submit(strings.MainMenu.START,
                                                          horz_alignment=internal.Alignment.CENTER,
                                                          vert_alignment=internal.Alignment.CENTER)

        options_button = self.out.overlays.menu.submit(strings.MainMenu.OPTIONS,
                                                       horz_alignment=internal.Alignment.CENTER,
                                                       vert_alignment=internal.Alignment.BOTTOM)

        def callback(menu_results):
            button_menu_map = {map_select_button: internal.MenuIdentifiers.MAP_SELECT,
                               options_button: internal.MenuIdentifiers.OPTIONS}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            return menu_to_go_to

        return callback

    def _map_select(self):
        """Displays the menu to select a map."""
        map_names = maps.map_names()

        menu_list = self.out.overlays.menu.list(title=strings.MapSelectMenu.TITLE, entry_text=map_names, necessary=True)
        game_start_button = self.out.overlays.menu.submit(strings.MapSelectMenu.SELECT_MAP)
        main_menu_button = self.out.overlays.menu.back(strings.MapSelectMenu.MAIN_MENU)

        def callback(menu_results):
            button_menu_map = {game_start_button: internal.MenuIdentifiers.GAME_START,
                               main_menu_button: internal.MenuIdentifiers.MAIN_MENU}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            if pressed_button is game_start_button:
                selected_index = menu_results[menu_list]
                map_name = map_names[selected_index]
                try:
                    map_name, tile_data, start_pos = maps.get_map_data_from_map_name(map_name, tiles.all_tiles())
                except exceptions.MapLoadException:
                    # TODO: Show error window
                    menu_to_go_to = internal.MenuIdentifiers.MAP_SELECT
                else:
                    self.map.load_tiles(tile_data)
                    # + 0.5 to move the player to center of the tile
                    self.player.set_pos(x=(start_pos.x + 0.5) * tiles.size,
                                        y=(start_pos.y + 0.5) * tiles.size,
                                        z=start_pos.z)

            return menu_to_go_to

        return callback

    def _options(self):
        main_menu_button = self.out.overlays.menu.back(strings.MapSelectMenu.MAIN_MENU)

        def callback(menu_results):
            button_menu_map = {main_menu_button: internal.MenuIdentifiers.MAIN_MENU}
            pressed_button, menu_to_go_to = self._standard_menu_movement(menu_results, button_menu_map)
            return menu_to_go_to

        return callback

    @staticmethod
    def _standard_menu_movement(menu_results, button_menu_map):
        pressed_buttons = [key for key in button_menu_map.keys() if menu_results[key]]
        if len(pressed_buttons) != 1:
            raise exceptions.ProgrammingException(strings.Exceptions.MENU_MOVE_WRONG)
        pressed_button = pressed_buttons[0]

        menu_to_go_to = button_menu_map[pressed_button]
        if menu_to_go_to is None:
            raise exceptions.ProgrammingException(strings.Exceptions.MENU_MOVE_WRONG)

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
        if self.map.fall(self.player):
            use_player_input = False
            self.player.fall_counter += 1
            if self.player.fall_counter == self.player.fall_speed:
                self._move_entity_vert(internal.Action.VERTICAL_DOWN, self.player)
                self.player.fall_counter = 0

        if use_player_input:
            for play_inp, input_type in inputs:
                if input_type == internal.InputTypes.ACTION:
                    self._action_entity(play_inp, self.player)
                elif input_type == internal.InputTypes.NO_INPUT:
                    pass
                else:
                    raise exceptions.ProgrammingException(strings.Exceptions.INVALID_INPUT_TYPE.format(input=input_type))

    def render(self):
        """Outputs the current game state."""
        self.out.overlays.game.reset()
        self.out.overlays.game(self.map.screens[self.player.z])
        self.out.overlays.game(self.player.appearance, (self.player.topleft_x, self.player.topleft_y))
        self.out.flush()

    def _action_entity(self, action, entity):
        vert_actions = {internal.Action.VERTICAL_UP, internal.Action.VERTICAL_DOWN}
        horz_actions = {internal.Move.LEFT, internal.Move.RIGHT, internal.Move.UP, internal.Move.DOWN}
        if action in vert_actions:
            self._move_entity_vert(action, entity)
        elif action in horz_actions:
            self._move_entity_rel(action, entity)
        else:
            raise exceptions.ProgrammingException(strings.Exceptions.BAD_ACTION.format(action=action))

    def _move_entity_vert(self, action, entity):
        vert_actions = {internal.Action.VERTICAL_UP: 1,
                        internal.Action.VERTICAL_DOWN: -1}
        direction = vert_actions[action]
        new_entity_pos = tools.Object(x=entity.x, y=entity.y, z=entity.z + direction)
        if direction == 1:
            if self.map.entity_wall_collide(entity, new_entity_pos) or self.map.entity_floor_collide(entity, new_entity_pos):
                return
        if direction == -1:
            if self.map.entity_wall_collide(entity, new_entity_pos) or self.map.entity_floor_collide(entity, entity.pos):
                return

        entity.z += direction

        # current_pos = entity.grid_pos
        # old_tile = self.map[current_pos]
        # if action == internal.Action.VERTICAL_UP:
        #     dir = 1
        # else:  # Move down
        #     dir = -1
        #
        # new_entity_pos = tools.Object(x=current_pos.x, y=current_pos.y, z=current_pos.z + dir)
        # if self.map.entity_wall_collide(entity, new_entity_pos):
        #     return
        #
        # new_tile = self.map[new_entity_pos]
        #
        # if action == internal.Action.VERTICAL_UP:
        #     if new_tile.floor and not entity.incorporeal:
        #         return  # Corporeal entities cannot pass through solid floors
        #     if not ((old_tile.suspend_up and new_tile.suspend_down) or entity.flight):
        #         return  # Flightless entities require a suspension to move vertically upwards
        #
        # else:  # Move down
        #     if old_tile.floor and not entity.incorporeal:
        #         return  # Corporeal entities cannot pass through solid floors
        #
        # entity.z += dir

    def _move_entity_rel(self, action, entity):
        horz_actions = {internal.Move.LEFT: tools.Object(x=-1, y=0),
                        internal.Move.RIGHT: tools.Object(x=1, y=0),
                        internal.Move.UP: tools.Object(x=0, y=-1),
                        internal.Move.DOWN: tools.Object(x=0, y=1)}
        direction = horz_actions[action]
        scaling = entity.speed / math.sqrt(direction.x ** 2 + direction.y ** 2)
        new_entity_pos = tools.Object(x=entity.x + direction.x * scaling,
                                      y=entity.y + direction.y * scaling,
                                      z=entity.z)
        if not self.map.entity_wall_collide(entity, new_entity_pos):
            entity.x = new_entity_pos.x
            entity.y = new_entity_pos.y

    def _move_entity_abs(self, pos, entity):
        direction = tools.Object(x=pos.x - entity.x, y=pos.y - entity.y)
        self._move_entity_rel(direction, entity)
