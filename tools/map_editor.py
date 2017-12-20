"""A map editor for the game!"""

import itertools
import math
import PIL.Image
import PIL.ImageTk
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import Tools as tools


import Game.config.internal as internal
import Game.config.strings as strings

import Game.data.maps as maps

import Game.program.tiles as tiles
import Game.program.misc.exceptions as exceptions
import Game.program.misc.sdl as sdl


class TkTileMixin(tiles.TileBase):
    """Added to all the tile classes to give them the enhanced functionality needed to be used in the map editor."""

    def __init_subclass__(cls, **kwargs):
        super(TkTileMixin, cls).__init_subclass__(**kwargs)
        # We can scroll through the different appearances before placing a tile; the current selection is stored here
        # (as an integer) as 'appearance_lookup_index'.
        cls.appearance_lookup_names = list(cls.appearances.keys())
        cls.appearance_lookup_index = 0

        # Pygame uses Surfaces, but they're not understood by tkinter. So here we take every surface we might possibly
        # have and convert them to a tkinter-understandable PhotoImage. The results are stored as values in
        # 'tk_all_appearances', with the key being the id of the Surface they originally came from.
        cls.tk_all_appearances = {}
        if cls.can_rotate:
            rotated_surfs = itertools.chain(cls.left_appearances.values(), cls.right_appearances.values(),
                                    cls.down_appearances.values())
        else:
            rotated_surfs = []
        for surf in itertools.chain(cls.appearances.values(), rotated_surfs):
            cls.tk_all_appearances[id(surf)] = cls.surf_to_tk(surf)

    def __init__(self, **kwargs):
        if 'appearance_lookup' not in kwargs:
            kwargs['appearance_lookup'] = self.appearance_lookup_names[self.appearance_lookup_index]
        super(TkTileMixin, self).__init__(**kwargs)

    @property
    def tk_appearance(self):
        """The tkinter version of the tile's appearance."""
        return self.tk_all_appearances[id(self.appearance)]

    @tools.classproperty
    def cls_appearance(cls):
        """Gives the class a notion of appearance.

        In the main game, appearance is a property so we can't acces it from the class. Here we just pick the first
        appearance."""

        first_appearance = list(cls.appearances.values())[cls.appearance_lookup_index]
        return cls.tk_all_appearances[id(first_appearance)]

    @staticmethod
    def surf_to_tk(surface):
        """Converts a pygame.Surface into a tkinter-understandable PhotoImage."""

        image_str = sdl.image.tostring(surface, 'RGB')
        surf_rect = surface.get_rect()
        width, height = surf_rect.width, surf_rect.height
        return PIL.ImageTk.PhotoImage(PIL.Image.frombytes('RGB', (width, height), image_str))

    @classmethod
    def scroll_appearance(cls, button):
        """Changes which appearance of multiple-appearance classes we'll be placing."""

        def _scroll_appearance(event):
            # Change what we'll be placing
            all_appearances = list(cls.appearances.values())
            cls.appearance_lookup_index += {True: -1, False: 1}[event.delta > 0]
            cls.appearance_lookup_index %= len(all_appearances)

            # And update the button
            appearance = all_appearances[cls.appearance_lookup_index]
            tk_appearance = cls.tk_all_appearances[id(appearance)]
            button.config(image=tk_appearance)

        return _scroll_appearance

    def serialize(self):
        """Serialize the tile data - tile type, rotation, appearance etc. - into a str of a dict, for saving."""

        returnval = {'def': self.definition}

        opts = {}
        if self.can_rotate:
            opts['rotation'] = self.rotation
        if len(self.appearances) != 1:
            # Our save file parser, ast.literal_eval, can't handle frozensets, so we convert them to regular sets first.
            # As self.appearance_lookup is a dictionary key, it can only be a frozenset, not a set, so this change is
            # unambiguous; we'll switch it back when we load a file.
            # Nonetheless this seems a bit hacky.
            if isinstance(self.appearance_lookup, frozenset):
                appearance_lookup = set(self.appearance_lookup)
            else:
                appearance_lookup = self.appearance_lookup
            opts['appearance_lookup'] = appearance_lookup

        if opts:
            returnval['opts'] = opts
        return str(returnval)


class MainApplication:
    """The main map editor application."""

    background_color = 'white'

    def __init__(self, tk, tk_tile_types):
        self._tk = tk
        self._tk_tile_types = tk_tile_types

        # Just keeping a reference to those images we don't otherwise want to keep a reference to, to prevent them from
        # being garbage collected
        self._store = []

        # Which tile we're currently placing. None = deleting tiles.
        # Can take special values, e.g. for placing the starting position.
        self._current_tile = None
        # A reference to the callback when resizing etc. the main window.
        self._config_callback = None
        # The last grid location we placed a tile in, so we know we don't have to place another one there during every
        # tick of a mouse drag.
        self._last_grid_loc = tools.Object(tile_x=None, tile_y=None)

        # The menu on the right
        self._menu = tkinter.Frame(tk, relief=tkinter.RIDGE, borderwidth=2)
        self._menu.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=0)

        # The clear and save buttons
        self._file_frame = tkinter.Frame(self._menu, relief=tkinter.RIDGE, borderwidth=3)
        self._new_button = tkinter.Button(self._file_frame, text=strings.MapEditor.NEW, width=5, command=self.new)
        self._open_button = tkinter.Button(self._file_frame, text=strings.MapEditor.OPEN, width=5, command=self.open)
        self._save_button = tkinter.Button(self._file_frame, text=strings.MapEditor.SAVE, width=5, command=self.save)
        self._file_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self._new_button.pack(side=tkinter.LEFT)
        self._open_button.pack(side=tkinter.LEFT)
        self._save_button.pack(side=tkinter.LEFT)

        # The level name panel
        self._level_name_frame = tkinter.Frame(self._menu, relief=tkinter.RIDGE, borderwidth=3)
        self._level_name_label = tkinter.Label(self._level_name_frame, text=strings.MapEditor.MAP_NAME_PROMPT)
        self._level_name_entry = tkinter.Entry(self._level_name_frame)
        self._level_name_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self._level_name_label.pack(side=tkinter.TOP)
        self._level_name_entry.pack(side=tkinter.LEFT, fill=tkinter.X)

        # The placing-the-player-start-position panel
        self._start_pos_frame = tkinter.Frame(self._menu, relief=tkinter.RIDGE, borderwidth=3)
        self._start_pos_button = tkinter.Button(self._start_pos_frame, text=strings.MapEditor.SET_START_POS,
                                                command=self.set_tile(internal.MapEditor.START_POS))
        self._start_pos_image = PIL.ImageTk.PhotoImage(file=internal.MapEditor.START_POS_MARKER)
        self._start_pos_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self._start_pos_button.pack(side=tkinter.TOP)

        # The panel for changing z level.
        self._z_button_frame = tkinter.Frame(self._menu, relief=tkinter.RIDGE, borderwidth=3)
        self._z_level_label = tkinter.Label(self._z_button_frame, text=strings.MapEditor.CHANGE_Z_LEVEL)
        self._cur_z_level_label = tkinter.Label(self._z_button_frame,
                                                text=strings.MapEditor.CURRENT_Z_LEVEL + "0")
        self._up_z_button = tkinter.Button(self._z_button_frame, text='  +  ', command=self.up_z_level)
        self._down_z_button = tkinter.Button(self._z_button_frame, text='  -  ', command=self.down_z_level)
        self._z_button_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self._z_level_label.grid(row=0, column=0)
        self._up_z_button.grid(row=0, column=1)
        self._down_z_button.grid(row=0, column=2)
        self._cur_z_level_label.grid(row=1, columnspan=3)

        # The frame for selecting tiles to place
        self.tile_select_frame = tkinter.Frame(self._menu, relief=tkinter.RIDGE, borderwidth=3)
        self.tile_select_frame.pack(fill=tkinter.BOTH, expand=1)

        # The delete-tile button
        # Ugly hack to make the button be the right size. Sadly this is one of the saner ways of accomplishing this.
        empty_image = PIL.ImageTk.PhotoImage(file=internal.MapEditor.EMPTY)
        self._store.append(empty_image)
        delete_button = tkinter.Button(self.tile_select_frame, image=empty_image,
                                       command=self.set_tile(None))
        delete_button.grid(row=0, column=0)
        delete_button_name = tkinter.Label(self.tile_select_frame, text=strings.MapEditor.DELETE_TILE)
        delete_button_name.grid(row=0, column=1)

        # The buttons for selecting which tile to place
        for i, tk_tile_type in enumerate(self._tk_tile_types.values()):
            tile_button = tkinter.Button(self.tile_select_frame, image=tk_tile_type.cls_appearance,
                                         command=self.set_tile(tk_tile_type))
            tile_button_name = tkinter.Label(self.tile_select_frame, text=tk_tile_type.name)
            tile_button.grid(row=i + 1, column=0)
            tile_button_name.grid(row=i + 1, column=1)
            # Allow us to scroll through appearances using the mouse wheel
            tile_button.bind("<MouseWheel>", self.scroll_on_button(tk_tile_type, tile_button))

        # The main canvas we're placing elements on.
        self._canvas = tkinter.Canvas(tk, background=self.background_color)
        self._canvas.bind("<Button-1>", self.place_tile)  # Place a tile
        self._canvas.bind("<B1-Motion>", self.place_tile_drag)  # Place many tiles
        self._canvas.bind("<Button-2>", self.canvas_mark)  # Drag the canvas around
        self._canvas.bind("<B2-Motion>", self.canvas_move)  #
        self._canvas.bind("<Button-3>", self.rotate_tile)   # Rotate a tile
        self._canvas.bind("<MouseWheel>", self.scroll_z_level)  # Change z level
        self._canvas.pack(fill=tkinter.BOTH, expand=1)
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

        # For when we resize the window.
        self._tk.bind("<Configure>", self.on_config)

        # Defined here so that they're in __init__; immediately redefined in reset() below.
        # Whether or not we've saved since the last edit
        self.have_saved = True
        # The tiles that have been placed down
        self._tile_data_dict = None
        # The current z level we're displaying and working on
        self._z_level = None
        # The starting position of the player
        self._start_pos = None
        # The image on the canvas marking the starting position of the player.
        self._start_pos_marker = None
        # The grid lines on the canvas
        self._grid_lines = None
        # The other images on the canvas. (i.e. the tiles)
        self._canvas_images = None
        self.reset()

    def reset(self):
        """Resets the map editor back to its default state."""
        self.have_saved = True
        self._tile_data_dict = tools.deldefaultdict(lambda: tools.deldict())
        self._z_level = 0
        self._start_pos = None
        self._start_pos_marker = None
        self._grid_lines = []
        self._canvas_images = {}
        self.refresh_canvas()
        self._level_name_entry.delete(0, tkinter.END)

    def scroll_on_button(self, tile_type, tile_button):
        """Changes which appearance of multiple-appearance tiles we'll be placing."""

        def _scroll_on_button(event):
            self.set_tile(tile_type)()
            tile_type.scroll_appearance(tile_button)(event)
        return _scroll_on_button

    def scroll_z_level(self, event):
        """Change which z level we're on."""

        if event.delta > 0:
            self.up_z_level()
        else:
            self.down_z_level()

    def up_z_level(self):
        """Move up a z level."""

        self._z_level += 1
        self._cur_z_level_label.config(text=strings.MapEditor.CURRENT_Z_LEVEL + str(self._z_level))
        self.refresh_canvas()

    def down_z_level(self):
        """Move down a z level."""

        self._z_level -= 1
        self._cur_z_level_label.config(text=strings.MapEditor.CURRENT_Z_LEVEL + str(self._z_level))
        self.refresh_canvas()

    def refresh_canvas(self):
        """Update the canvas."""

        self._canvas.delete(tkinter.ALL)
        if self._z_level in self._tile_data_dict:
            for pos, tile in self._tile_data_dict[self._z_level].items():
                id_ = self._canvas.create_image((pos[0] * tiles.size, pos[1] * tiles.size),
                                                image=tile.tk_appearance,
                                                anchor=tkinter.NW)
                self._canvas_images[(pos[0], pos[1])] = id_
        self.place_start_pos_marker()
        self.canvas_tile_grid()

    def set_start_pos(self, x, y, z):
        """Sets the starting position."""
        self._start_pos = tools.Object(x=x, y=y, z=z)

    def place_start_pos_marker(self):
        """Place the marker for the starting position"""

        if self._start_pos_marker is not None:
            self._canvas.delete(self._start_pos_marker)
        if self._start_pos is not None:
            if self._start_pos.z == self._z_level:
                self._start_pos_marker = self._canvas.create_image((self._start_pos.x * tiles.size,
                                                                    self._start_pos.y * tiles.size),
                                                                   image=self._start_pos_image, anchor=tkinter.NW)

    def on_config(self, event):
        """Called every time the window changes size"""

        # Only call it after ten milliseconds
        if self._config_callback is not None:
            self._tk.after_cancel(self._config_callback)
        self._config_callback = self._tk.after(10, self.canvas_tile_grid)  # Redo the grid lines on the canvas

    def set_tile(self, tile):
        """Set which tile we're placing."""

        def set_tile_action():
            self._current_tile = tile
        return set_tile_action

    def canvas_mark(self, event):
        """For dragging the canvas around."""
        self._canvas.scan_mark(event.x, event.y)

    def canvas_move(self, event):
        """Drag the canvas around."""

        self._canvas.scan_dragto(event.x, event.y, gain=1)
        self.canvas_tile_grid()
        self._tk.update_idletasks()

    def place_tile(self, event):
        """Place a tile at the target location on the canvas."""

        grid_loc = self.click_to_grid(event)
        self._place_tile(grid_loc)

    def place_tile_drag(self, event):
        """Place tiles whilst dragging the mouse."""

        grid_loc = self.click_to_grid(event)
        if grid_loc.tile_x != self._last_grid_loc.tile_x or grid_loc.tile_y != self._last_grid_loc.tile_y:
            self._place_tile(grid_loc)

    def _place_tile(self, grid_loc):
        """Place a tile at the particular grid location."""
        self.have_saved = False
        self._last_grid_loc = grid_loc

        if self._current_tile == internal.MapEditor.START_POS:  # Place the start marker
            self.set_start_pos(x=grid_loc.tile_x, y=grid_loc.tile_y, z=self._z_level)
            self.place_start_pos_marker()
        else:
            # If we're not placing the start marker, then delete the image that was already there.
            try:
                id_ = self._canvas_images[(grid_loc.tile_x, grid_loc.tile_y)]
            except KeyError:
                pass
            else:
                self._canvas.delete(id_)
                del self._canvas_images[(grid_loc.tile_x, grid_loc.tile_y)]

            if self._current_tile is None:  # Delete current tile
                # Deleting from the internal store
                del self._tile_data_dict[self._z_level][(grid_loc.tile_x, grid_loc.tile_y)]
                if not self._tile_data_dict[self._z_level]:
                    del self._tile_data_dict[self._z_level]
            else:
                # Overwriting in the internal store
                this_tile = self._current_tile()
                self._tile_data_dict[self._z_level][(grid_loc.tile_x, grid_loc.tile_y)] = this_tile
                # Place the new canvas image
                id_ = self._canvas.create_image((grid_loc.x, grid_loc.y), image=this_tile.tk_appearance,
                                                anchor=tkinter.NW)
                self._canvas.tag_lower(id_)  # Below the grid lines
                self._canvas_images[(grid_loc.tile_x, grid_loc.tile_y)] = id_

    def rotate_tile(self, event):
        """Rotate the tile in the specified location."""

        grid_loc = self.click_to_grid(event)
        try:
            tile = self._tile_data_dict[self._z_level][(grid_loc.tile_x, grid_loc.tile_y)]
        except KeyError:
            pass
        else:
            if tile.can_rotate:
                self.have_saved = False
                # Rotate the tile
                tile.next_rotate()
                # Update the appearance on the canvas
                self._canvas.delete(self._canvas_images[(grid_loc.tile_x, grid_loc.tile_y)])
                id_ = self._canvas.create_image((grid_loc.x, grid_loc.y), image=tile.tk_appearance,
                                                anchor=tkinter.NW)
                self._canvas.tag_lower(id_)
                self._canvas_images[(grid_loc.tile_x, grid_loc.tile_y)] = id_

    def click_to_grid(self, event):
        """Convert a click event into a position on the grid we impose on the canvas."""

        canvas_x = self._canvas.canvasx(event.x)
        canvas_y = self._canvas.canvasy(event.y)
        tile_x = math.floor(canvas_x / tiles.size)
        tile_y = math.floor(canvas_y / tiles.size)
        x = tile_x * tiles.size
        y = tile_y * tiles.size
        # x, y are the position on the canvas
        # tile_x, tile_y are the grid coordinates
        return tools.Object(x=x, y=y, tile_x=tile_x, tile_y=tile_y)

    def canvas_tile_grid(self):
        """Draw a grid on the canvas."""

        for id_ in self._grid_lines:
            self._canvas.delete(id_)
        self._grid_lines = []
        canvas_vis = self.canvas_visible_region()
        for x in range(tools.round_mult(canvas_vis.xmin, tiles.size, 'up'),
                       tools.round_mult(canvas_vis.xmax, tiles.size, 'down') + 1,
                       tiles.size):
            self._grid_lines.append(self._canvas.create_line(x, canvas_vis.ymin, x, canvas_vis.ymax))

        for y in range(tools.round_mult(canvas_vis.ymin, tiles.size, 'up'),
                       tools.round_mult(canvas_vis.ymax, tiles.size, 'down') + 1,
                       tiles.size):
            self._grid_lines.append(self._canvas.create_line(canvas_vis.xmin, y, canvas_vis.xmax, y))

    def canvas_offset(self):
        """Returns how much the canvas has moved from its original position. In particular it returns the coordinates
        of the top left of the visible region of the canvas. (So depending on your point of view this might be the
        negative of the offset.)"""

        x = self._canvas.canvasx(0)
        y = self._canvas.canvasy(0)
        return tools.Object(x=x, y=y)

    def canvas_visible_region(self):
        """Returns the canvas coordinates corresponding to the corners of the visible region of the canvas."""

        xmax = self._canvas.canvasx(self._canvas.winfo_width())
        ymax = self._canvas.canvasy(self._canvas.winfo_height())
        canvas_offset = self.canvas_offset()
        return tools.Object(xmax=xmax, ymax=ymax, xmin=canvas_offset.x, ymin=canvas_offset.y)

    def new(self):
        """Clear the canvas and reset."""

        if self.have_saved:
            res = tkinter.YES
        else:
            res = tkinter.messagebox.askyesno(strings.MapEditor.NEW_TITLE, strings.MapEditor.NEW_MESSAGE)
        if res == tkinter.YES:
            self.reset()

    def open(self):
        """Open a map file."""

        open_file = tkinter.filedialog.askopenfile(initialdir=internal.Maps.MAP_LOC,
                                                   title=strings.MapEditor.OPEN_TITLE,
                                                   filetypes=(('map files', '.map'), ('all files', '.*')))
        if open_file is not None:  # If they don't hit cancel
            try:
                with open_file:
                    map_name, tile_data, start_pos = \
                        maps.get_map_data_from_file(open_file, self._tk_tile_types,
                                                    tile_data_default=tools.deldefaultdict(lambda: tools.deldict()))
            except (OSError, exceptions.MapLoadException):
                tkinter.messagebox.showerror(strings.MapEditor.BAD_LOAD_TITLE, strings.MapEditor.BAD_LOAD_MESSAGE)
            else:
                self.reset()
                self._level_name_entry.insert(0, map_name)
                self._tile_data_dict = tile_data
                self.set_start_pos(x=start_pos.x, y=start_pos.y, z=start_pos.z)
                self.refresh_canvas()

    def save(self):
        """Save the current map."""

        try:
            map_name, tile_types, tile_data, start_pos = self.check_can_save()
        except exceptions.SaveException as e:
            tkinter.messagebox.showerror(strings.MapEditor.CANNOT_SAVE, str(e))
        else:
            save = str({'tile_types': tile_types, 'tile_data': tile_data, 'start_pos': start_pos}).replace(' ', '')
            save_file = tkinter.filedialog.asksaveasfile(
                initialdir=internal.Maps.MAP_LOC,
                initialfile=map_name + '.map',
                title='Save file',
                filetypes=(('map files', '.map'), ('all files', '.*')))
            if save_file is not None:  # If they don't hit cancel
                try:
                    with save_file:
                        save_file.write(save)
                except OSError:
                    tkinter.messagebox.showerror(strings.MapEditor.CANNOT_SAVE, strings.Exceptions.CANNOT_SAVE_FILE)
                else:
                    self.have_saved = True

    def check_can_save(self):
        """Whether or not we're trying to save a valid map. Will raise a SaveException if the map is invalid. Will
        return the objects for saving if valid."""

        if self._start_pos is None:
            raise exceptions.SaveException(strings.Exceptions.NO_START_POS)

        if self._start_pos.z not in self._tile_data_dict:
            raise exceptions.SaveException(strings.Exceptions.BAD_START_POS)
        if (self._start_pos.x, self._start_pos.y) not in self._tile_data_dict[self._start_pos.z]:
            raise exceptions.SaveException(strings.Exceptions.BAD_START_POS)

        map_name = self._level_name_entry.get().strip()
        if not map_name:
            raise exceptions.SaveException(strings.Exceptions.NO_MAP_SAVE_NAME)

        # We always normalise on saving so that we begin at x, y, z set to 0.
        x_min = y_min = z_min = math.inf
        for z_level, z_level_data in self._tile_data_dict.items():
            z_min = min(z_level, z_min)
            for x, y in z_level_data.keys():
                x_min = min(x, x_min)
                y_min = min(y, y_min)

        if math.inf in {x_min, y_min, z_min}:
            raise exceptions.SaveException(strings.Exceptions.NO_TILES)

        start_pos = (self._start_pos.x - x_min, self._start_pos.y - y_min, self._start_pos.z - z_min)

        tile_data = {}
        tile_types = []
        tile_type_to_index = {}
        for z_level, z_level_data in self._tile_data_dict.items():
            for (x, y), tile in z_level_data.items():
                serial_tile_data = tile.serialize()
                if serial_tile_data not in tile_types:
                    tile_types.append(serial_tile_data)
                    tile_type_to_index[serial_tile_data] = len(tile_types) - 1
                # Not using a defaultdict as we're going to take the str of tile_data and save it to file.
                tile_data.setdefault(z_level - z_min, {})[(x - x_min, y - y_min)] = tile_type_to_index[serial_tile_data]

        if not tile_data:
            # Should never get here, the earlier check that all of x,y,z min are not infinity should have already
            # handled this case. Buuuuuut just in case... ;)
            raise exceptions.SaveException(strings.Exceptions.NO_TILES)

        return map_name, tile_types, tile_data, start_pos


def start():
    tk = tkinter.Tk()
    tk.title(strings.MapEditor.WINDOW_TITLE)
    # Slightly evil hackery. A dictionary of Tk versions of all the tile types. The keys are the tile definitions.
    tk_tile_types = {def_: type('Tk' + tile_type.__name__, (TkTileMixin, tile_type), dict(name=tile_type.__name__))
                     for def_, tile_type in tiles.all_tiles().items()}

    map_editor = MainApplication(tk, tk_tile_types)

    def on_close():
        if map_editor.have_saved or tkinter.messagebox.askyesno(strings.MapEditor.QUIT_TITLE,
                                                                strings.MapEditor.QUIT_QUESTION) == tkinter.YES:
            tk.destroy()
    tk.protocol("WM_DELETE_WINDOW", on_close)
    tk.mainloop()


if __name__ == '__main__':
    start()
