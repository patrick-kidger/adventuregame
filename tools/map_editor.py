"""A somewhat rough and ready map editor!"""

import itertools
import math
import os
import PIL.Image
import PIL.ImageTk
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import Tools as tools


import Game.config.internal_strings as internal_strings

import Game.program.tiles as tiles
import Game.program.misc.sdl as sdl


# Must be pretty much the first thing called. i.e. even before we define the classes below.
tk = tkinter.Tk()


class SaveException(Exception):
    pass


class TkTileMixin:
    """Added to all the tile classes to give them the enhanced functionality needed to be used in the map editor.
    Not technically a mixin because we define a couple extra attributes, but hey, it's Python..."""

    def __init__(self, **kwargs):
        if self.has_multiple_appearances:
            appearance_lookup = list(self.appearances.keys())[self.current_geom_index]
        else:
            appearance_lookup = None
        super(TkTileMixin, self).__init__(appearance_lookup=appearance_lookup, **kwargs)

    def __init_subclass__(cls, **kwargs):
        super(TkTileMixin, cls).__init_subclass__(**kwargs)
        cls.current_geom_index = 0

        cls.tk_appearances = {}
        if hasattr(cls, 'appearances'):
            for surf in cls.appearances.values():
                cls.tk_appearances[id(surf)] = cls.surf_to_tk(surf)
            if cls.can_rotate:
                for surf in itertools.chain(cls.left_appearances.values(), cls.right_appearances.values(),
                                            cls.down_appearances.values()):
                    cls.tk_appearances[id(surf)] = cls.surf_to_tk(surf)
        else:
            cls.tk_appearances[id(cls.appearance)] = cls.surf_to_tk(cls.appearance)
            if cls.can_rotate:
                cls.tk_appearances[id(cls.left_appearance)] = cls.surf_to_tk(cls.left_appearance)
                cls.tk_appearances[id(cls.right_appearance)] = cls.surf_to_tk(cls.right_appearance)
                cls.tk_appearances[id(cls.down_appearance)] = cls.surf_to_tk(cls.down_appearance)

    @property
    def tk_appearance(self):
        return self.tk_appearances[id(self.appearance)]

    @property
    def rotated_tk_appearance(self):
        if self.can_rotate:
            return self.tk_appearances[id(self.rotated_appearance)]
        else:
            return self.tk_appearance

    @tools.classproperty
    def cls_appearance(cls):
        if hasattr(cls, 'appearances'):
            first_appearance = list(cls.appearances.values())[cls.current_geom_index]
            return cls.tk_appearances[id(first_appearance)]
        else:
            return cls.tk_appearances[id(cls.appearance)]

    @staticmethod
    def surf_to_tk(surface):
        image_str = sdl.image.tostring(surface, 'RGB')
        surf_rect = surface.get_rect()
        width, height = surf_rect.width, surf_rect.height
        return PIL.ImageTk.PhotoImage(PIL.Image.frombytes('RGB', (width, height), image_str))

    def next_rotate(self):
        if self.can_rotate:
            next_rotations = {internal_strings.TileRotation.UP: internal_strings.TileRotation.RIGHT,
                              internal_strings.TileRotation.RIGHT: internal_strings.TileRotation.DOWN,
                              internal_strings.TileRotation.DOWN: internal_strings.TileRotation.LEFT,
                              internal_strings.TileRotation.LEFT: internal_strings.TileRotation.UP}
            self.rotation = next_rotations[self.rotation]

    @classmethod
    def scroll_geometry(cls, button):
        def _scroll_geometry(event):
            if hasattr(cls, 'appearances'):
                all_appearances = list(cls.appearances.values())
                cls.current_geom_index += {True: -1, False: 1}[event.delta > 0]
                cls.current_geom_index %= len(all_appearances)
                appearance = all_appearances[cls.current_geom_index]
                tk_appearance = cls.tk_appearances[id(appearance)]
                button.config(image=tk_appearance)

        return _scroll_geometry

    def serialize(self):
        returnval = {'def': self.definition}

        opts = {}
        if self.can_rotate:
            opts['rotation'] = self.rotation
        if self.has_multiple_appearances:
            opts['appearance_lookup'] = self.appearance_lookup

        if opts:
            returnval['opts'] = opts
        return str(returnval)


class MainApplication:
    background_color = 'white'
    z_level_text = "Current z level: "

    def __init__(self):
        # Just keeping a reference to those images we don't otherwise want to keep a reference to, to prevent them from
        # being garbage collected
        self._store = []

        self.current_tile = None
        self.config_callback = None
        self.last_grid_loc = tools.Object(tile_x=None, tile_y=None)

        self.menu = tkinter.Frame(tk, relief=tkinter.RIDGE, borderwidth=2)
        self.menu.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=0)

        self.level_name_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.level_name_label = tkinter.Label(self.level_name_frame, text="Map name: ")
        self.level_name_entry = tkinter.Entry(self.level_name_frame)
        self.level_name_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self.level_name_label.pack(side=tkinter.TOP)
        self.level_name_entry.pack(side=tkinter.LEFT, fill=tkinter.X)

        self.start_pos_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.start_pos_button = tkinter.Button(self.start_pos_frame, text='Set start pos',
                                               command=self.set_tile('start_pos'))
        self.start_pos_image = PIL.ImageTk.PhotoImage(
            file=os.path.join(os.path.dirname(__file__), 'images', 'start_pos.png'))
        self.start_pos_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self.start_pos_button.pack(side=tkinter.TOP)

        self.file_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.new_button = tkinter.Button(self.file_frame, text='New', command=self.new)
        self.save_button = tkinter.Button(self.file_frame, text='Save', command=self.save)
        self.file_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.new_button.pack(side=tkinter.LEFT)
        self.save_button.pack(side=tkinter.LEFT)

        self.z_button_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.z_level_label = tkinter.Label(self.z_button_frame, text="Change z level:")
        self.cur_z_level_label = tkinter.Label(self.z_button_frame, text=self.z_level_text + "0")
        self.up_z_button = tkinter.Button(self.z_button_frame, text='  +  ', command=self.up_z_level)
        self.down_z_button = tkinter.Button(self.z_button_frame, text='  -  ', command=self.down_z_level)
        self.z_button_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.z_level_label.grid(row=0, column=0)
        self.up_z_button.grid(row=0, column=1)
        self.down_z_button.grid(row=0, column=2)
        self.cur_z_level_label.grid(row=1, columnspan=3)

        self.tile_select_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.tile_select_frame.pack(fill=tkinter.BOTH, expand=1)

        # Ugly hack to make the button be the right size. Sadly this is one of the saner ways of accomplishing this.
        empty_image = PIL.ImageTk.PhotoImage(file=os.path.join(os.path.dirname(__file__), 'images', 'empty.png'))
        self._store.append(empty_image)
        delete_button = tkinter.Button(self.tile_select_frame, image=empty_image,
                                       command=self.set_tile(None))
        delete_button.grid(row=0, column=0)
        delete_button_name = tkinter.Label(self.tile_select_frame, text='Delete tile')
        delete_button_name.grid(row=0, column=1)

        for i, tile_type in enumerate(tiles.all_tiles().values()):
            # Evil hackery
            tk_tile_type = type('Tk' + tile_type.__name__, (TkTileMixin, tile_type), dict(name=tile_type.__name__))
            tile_button = tkinter.Button(self.tile_select_frame, image=tk_tile_type.cls_appearance,
                                         command=self.set_tile(tk_tile_type))
            tile_button_name = tkinter.Label(self.tile_select_frame, text=tk_tile_type.name)
            tile_button.grid(row=i + 1, column=0)
            tile_button_name.grid(row=i + 1, column=1)
            if hasattr(tk_tile_type, 'appearances'):
                tile_button.bind("<MouseWheel>", self.scroll_on_button(tk_tile_type, tile_button))

        self.canvas = tkinter.Canvas(tk, background=self.background_color)
        self.canvas.bind("<Button-1>", self.place_tile)
        self.canvas.bind("<B1-Motion>", self.place_tile_drag)
        self.canvas.bind("<Button-2>", self.canvas_click)
        self.canvas.bind("<B2-Motion>", self.canvas_move)
        self.canvas.bind("<Button-3>", self.rotate_tile)
        self.canvas.bind("<MouseWheel>", self.scroll_z_level)
        self.canvas.pack(fill=tkinter.BOTH, expand=1)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        tk.bind("<Configure>", self.on_config)

        self.reset()

    def reset(self):
        self.have_saved = True
        self.tile_data_dict = tools.deldefaultdict(lambda: tools.deldict())
        self.z_level = 0
        self.start_pos = None
        self.start_pos_marker = None
        self.grid_lines = []
        self.canvas_images = {}
        self.refresh_canvas()
        self.level_name_entry.delete(0, tkinter.END)

    def scroll_on_button(self, tile_type, tile_button):
        def _scroll_on_button(event):
            self.set_tile(tile_type)()
            tile_type.scroll_geometry(tile_button)(event)

        return _scroll_on_button

    def scroll_z_level(self, event):
        if event.delta > 0:
            self.up_z_level()
        else:
            self.down_z_level()

    def up_z_level(self):
        self.z_level += 1
        self.cur_z_level_label.config(text=self.z_level_text + str(self.z_level))
        self.refresh_canvas()

    def down_z_level(self):
        self.z_level -= 1
        self.cur_z_level_label.config(text=self.z_level_text + str(self.z_level))
        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas.delete(tkinter.ALL)
        if self.z_level in self.tile_data_dict:
            for pos, tile in self.tile_data_dict[self.z_level].items():
                id_ = self.canvas.create_image((pos[0] * tiles.size, pos[1] * tiles.size),
                                               image=tile.rotated_tk_appearance,
                                               anchor=tkinter.NW)
                self.canvas_images[(pos[0], pos[1])] = id_
        self.place_start_pos_marker()
        self.canvas_tile_grid()

    def place_start_pos_marker(self):
        if self.start_pos_marker is not None:
            self.canvas.delete(self.start_pos_marker)
        if self.start_pos is not None:
            if self.start_pos.z == self.z_level:
                self.start_pos_marker = self.canvas.create_image((self.start_pos.x * tiles.size,
                                                                  self.start_pos.y * tiles.size),
                                                                 image=self.start_pos_image, anchor=tkinter.NW)

    def on_config(self, event):
        if self.config_callback is not None:
            tk.after_cancel(self.config_callback)
        self.config_callback = tk.after(10, self.canvas_tile_grid)

    def set_tile(self, tile):
        def set_tile_action():
            self.current_tile = tile

        return set_tile_action

    def canvas_click(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def canvas_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.canvas_tile_grid()
        tk.update_idletasks()

    def place_tile(self, event):
        grid_loc = self.click_to_grid(event)
        self._place_tile(grid_loc)

    def place_tile_drag(self, event):
        grid_loc = self.click_to_grid(event)
        if grid_loc.tile_x != self.last_grid_loc.tile_x or grid_loc.tile_y != self.last_grid_loc.tile_y:
            self._place_tile(grid_loc)
            self.last_grid_loc = grid_loc

    def _place_tile(self, grid_loc):
        self.have_saved = False
        if self.current_tile != 'start_pos':
            try:
                id_ = self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)]
            except KeyError:
                pass
            else:
                self.canvas.delete(id_)
                del self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)]

        if self.current_tile is None:
            del self.tile_data_dict[self.z_level][(grid_loc.tile_x, grid_loc.tile_y)]
            if not self.tile_data_dict[self.z_level]:
                del self.tile_data_dict[self.z_level]
        elif self.current_tile == 'start_pos':
            self.start_pos = tools.Object(x=grid_loc.tile_x, y=grid_loc.tile_y, z=self.z_level)
            self.place_start_pos_marker()
        else:
            this_tile = self.current_tile(pos=tools.Object(x=grid_loc.tile_x, y=grid_loc.tile_y, z=self.z_level))
            self.tile_data_dict[self.z_level][(grid_loc.tile_x, grid_loc.tile_y)] = this_tile
            id_ = self.canvas.create_image((grid_loc.x, grid_loc.y), image=this_tile.tk_appearance,
                                           anchor=tkinter.NW)
            self.canvas.tag_lower(id_)
            self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)] = id_

    # def convert_stair(self, this_tile, grid_loc):
    #     this_tile_needs_updating = False
    #
    #     # To prevent the defaultdict behaviour from creating an empty z-level
    #     if self.z_level + 1 in self.tile_data_dict:
    #         try:
    #             above_tile = self.tile_data_dict[self.z_level + 1][(grid_loc.tile_x, grid_loc.tile_y)]
    #         except KeyError:
    #             pass
    #         else:
    #             if isinstance(above_tile, stair_tile) and not above_tile.floor:
    #                 if this_tile is not None:
    #                     this_tile.adj_stairs.add(internal_strings.StairAdjacency.VERTICAL_UP)
    #                     above_tile.adj_stairs.add(internal_strings.StairAdjacency.VERTICAL_DOWN)
    #                     this_tile_needs_updating = True
    #                 else:
    #                     above_tile.adj_stairs.remove(internal_strings.StairAdjacency.VERTICAL_DOWN)
    #                 above_tile.convert_stair()
    #                 above_tile.update_tk_appearance()
    #
    #     # To prevent the defaultdict behaviour from creating an empty z-level
    #     if self.z_level - 1 in self.tile_data_dict:
    #         try:
    #             below_tile = self.tile_data_dict[self.z_level - 1][(grid_loc.tile_x, grid_loc.tile_y)]
    #         except KeyError:
    #             pass
    #         else:
    #             if isinstance(below_tile, stair_tile) and not this_tile.floor:
    #                 if this_tile is not None:
    #                     this_tile.adj_stairs.add(internal_strings.StairAdjacency.VERTICAL_DOWN)
    #                     below_tile.adj_stairs.add(internal_strings.StairAdjacency.VERTICAL_UP)
    #                     this_tile_needs_updating = True
    #                 else:
    #                     below_tile.adj_stairs.remove(internal_strings.StairAdjacency.VERTICAL_UP)
    #                 below_tile.convert_stair()
    #                 below_tile.update_tk_appearance()
    #
    #     if this_tile_needs_updating:
    #         this_tile.convert_stair()
    #         this_tile.update_tk_appearance()

    def rotate_tile(self, event):
        grid_loc = self.click_to_grid(event)
        try:
            tile = self.tile_data_dict[self.z_level][(grid_loc.tile_x, grid_loc.tile_y)]
        except KeyError:
            pass
        else:
            if tile.can_rotate:
                self.have_saved = False
                tile.next_rotate()
                self.canvas.delete(self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)])
                id_ = self.canvas.create_image((grid_loc.x, grid_loc.y), image=tile.rotated_tk_appearance,
                                               anchor=tkinter.NW)
                self.canvas.tag_lower(id_)
                self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)] = id_

    def click_to_grid(self, click):
        canvas_x = self.canvas.canvasx(click.x)
        canvas_y = self.canvas.canvasy(click.y)
        tile_x = math.floor(canvas_x / tiles.size)
        tile_y = math.floor(canvas_y / tiles.size)
        x = tile_x * tiles.size
        y = tile_y * tiles.size
        return tools.Object(x=x, y=y, tile_x=tile_x, tile_y=tile_y)

    def canvas_tile_grid(self):
        for id_ in self.grid_lines:
            self.canvas.delete(id_)
        self.grid_lines = []
        canvas_vis = self.canvas_visible_region()
        for x in range(tools.round_mult(canvas_vis.xmin, tiles.size, 'up'),
                       tools.round_mult(canvas_vis.xmax, tiles.size, 'down') + 1,
                       tiles.size):
            self.grid_lines.append(self.canvas.create_line(x, canvas_vis.ymin, x, canvas_vis.ymax))

        for y in range(tools.round_mult(canvas_vis.ymin, tiles.size, 'up'),
                       tools.round_mult(canvas_vis.ymax, tiles.size, 'down') + 1,
                       tiles.size):
            self.grid_lines.append(self.canvas.create_line(canvas_vis.xmin, y, canvas_vis.xmax, y))

    def canvas_offset(self):
        x = -1 * self.canvas.canvasx(0)
        y = -1 * self.canvas.canvasy(0)
        return tools.Object(x=x, y=y)

    def canvas_visible_region(self):
        xmax = self.canvas.canvasx(self.canvas.winfo_width())
        ymax = self.canvas.canvasy(self.canvas.winfo_height())
        canvas_offset = self.canvas_offset()
        return tools.Object(xmax=xmax, ymax=ymax, xmin=-1 * canvas_offset.x, ymin=-1 * canvas_offset.y)

    def new(self):
        if self.have_saved:
            res = tkinter.YES
        else:
            res = tkinter.messagebox.askyesno('Clear map?', 'Do you want to clear the map you are currently working on?')
        if res == tkinter.YES:
            self.reset()

    def save(self):
        try:
            map_name, tile_data, tile_types = self.check_can_save()
        except SaveException:
            # produce an error message
            pass
        else:
            start_pos = (self.start_pos.x, self.start_pos.y, self.start_pos.z)
            save = str({'map_name': map_name, 'tile_types': tile_types, 'tile_data': tile_data, 'start_pos': start_pos})
            save_file = tkinter.filedialog.asksaveasfile(
                initialdir=os.path.join(os.path.dirname(__file__), '..', 'data', 'map_data'),
                initialfile='my_map.map',
                title='Save file',
                filetypes=(('map files', '.map'), ('all files', '.*')))
            with save_file as f:
                f.write(save)
            self.have_saved = True

    def check_can_save(self):
        if self.start_pos is None:
            raise SaveException

        map_name = self.level_name_entry.get().strip()
        if not map_name:
            raise SaveException

        tile_data = {}
        tile_types = []
        tile_type_to_index = {}
        for z_level, z_level_data in self.tile_data_dict.items():
            for pos, tile in z_level_data.items():
                serial_tile_data = tile.serialize()
                if serial_tile_data not in tile_types:
                    tile_types.append(serial_tile_data)
                    tile_type_to_index[serial_tile_data] = len(tile_types) - 1
                tile_data.setdefault(z_level, {})[pos] = tile_type_to_index[serial_tile_data]

        if not tile_data:
            raise SaveException

        if self.start_pos.z not in tile_data:
            raise SaveException
        if (self.start_pos.x, self.start_pos.y) not in tile_data[self.start_pos.z]:
            raise SaveException

        return map_name, tile_data, tile_types


if __name__ == '__main__':
    # app reference to prevent garbage collection
    app = MainApplication()
    tk.mainloop()
