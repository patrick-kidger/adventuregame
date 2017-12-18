"""A somewhat rough and ready map editor!"""

import json
import math
import os
import PIL.Image
import PIL.ImageTk
import tkinter
import Tools as tools


import Game.config.config as config
import Game.config.internal_strings as internal_strings

import Game.program.tiles as tiles


tk = tkinter.Tk()


class SaveException(Exception):
    pass


class TileTypes:
    def __init__(self, tile_class):
        self.appearance_filename = tile_class.appearance_filename
        self.appearance = None
        self.left_appearance = None
        self.right_appearance = None
        self.down_appearance = None
        self.name = tile_class.__name__
        self.definition = tile_class.definition
        self.can_rotate = tile_class.can_rotate

    def set_appearance(self, image):
        # Ideally we'd generate these dynamically as we need them, but since we have to store a reference to them anyway
        # to prevent them being garbage collected, it's simpler to just store them from the get-go rather than cache
        # them as they're generated. (Also means we don't need to store the original image; it's not possible to rotate
        # a PhotoImage.)
        self.appearance = PIL.ImageTk.PhotoImage(image)
        if self.can_rotate:
            self.left_appearance = PIL.ImageTk.PhotoImage(image.rotate(90))
            self.down_appearance = PIL.ImageTk.PhotoImage(image.rotate(180))
            self.right_appearance = PIL.ImageTk.PhotoImage(image.rotate(-90))


tile_types = {key: TileTypes(val) for key, val in tiles.all_tiles().items()}
for tile in tile_types.values():
    appearance_file_path = os.path.join(os.path.dirname(__file__), '..', 'images',
                                        *config.TILE_FOLDER.split('/'),
                                        *tile.appearance_filename.split('/'))
    tile.set_appearance(PIL.Image.open(appearance_file_path))


class TileData:
    def __init__(self):
        self.tile_type = tile_types[' ']
        self.rotate = internal_strings.TileRotation.UP
        self.opts = {}

    def set(self, tile_type):
        self.tile_type = tile_type

    def next_rotate(self):
        next_rotations = {internal_strings.TileRotation.UP: internal_strings.TileRotation.RIGHT,
                          internal_strings.TileRotation.RIGHT: internal_strings.TileRotation.DOWN,
                          internal_strings.TileRotation.DOWN: internal_strings.TileRotation.LEFT,
                          internal_strings.TileRotation.LEFT: internal_strings.TileRotation.UP}
        self.rotate = next_rotations[self.rotate]

    def rotated_appearance(self):
        rot_appearance = {internal_strings.TileRotation.UP: self.tile_type.appearance,
                          internal_strings.TileRotation.RIGHT: self.tile_type.right_appearance,
                          internal_strings.TileRotation.DOWN: self.tile_type.down_appearance,
                          internal_strings.TileRotation.LEFT: self.tile_type.left_appearance}
        return rot_appearance[self.rotate]

    def to_json(self):
        if self.tile_type.can_rotate:
            self.opts['rot'] = self.rotate
        return {'def': self.tile_type.definition, 'opts': self.opts}


class MainApplication:
    background_color = 'white'
    place_tol = 7  # How many pixels the canvas has to be moved for the click event to not place a tile.
    z_level_text = "Current z level: "

    def __init__(self):
        # Just keeping a reference to everything that we don't actually need a reference for - this prevents them from
        # being garbage collected (which obviously we don't want)
        self._store = []

        self.current_tile = None
        self.tile_data_dict = tools.deldefaultdict(lambda: tools.deldefaultdict(TileData))
        self.config_callback = None
        self.mouse_click_pos = tools.Object(x=0, y=0)
        self.z_level = 0
        self.start_pos = None
        self.start_pos_marker = None
        self.grid_lines = []
        self.canvas_images = {}

        self.menu = tkinter.Frame(tk, relief=tkinter.RIDGE, borderwidth=2)
        self.menu.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=0)

        self.level_name_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.level_name_label = tkinter.Label(self.level_name_frame, text="Map name: ")
        self.level_name_entry = tkinter.Entry(self.level_name_frame)
        self.level_name_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self.level_name_label.pack(side=tkinter.TOP)
        self.level_name_entry.pack(side=tkinter.LEFT, fill=tkinter.X)

        self.start_pos_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.start_pos_button = tkinter.Button(self.start_pos_frame, text='Set start pos', command=self.set_tile('start_pos'))
        self.start_pos_image = PIL.ImageTk.PhotoImage(file=os.path.join(os.path.dirname(__file__), 'images', 'start_pos.png'))
        self.start_pos_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self.start_pos_button.pack(side=tkinter.TOP)

        self.save_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.save_button = tkinter.Button(self.save_frame, text='Save', command=self.save)
        self.save_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.save_button.pack()

        self.z_button_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        self.z_level_label = tkinter.Label(self.z_button_frame, text="Change z level:")
        self.cur_z_level_label = tkinter.Label(self.z_button_frame, text=self.z_level_text + str(self.z_level))
        self.up_z_button = tkinter.Button(self.z_button_frame, text='  +  ', command=self.up_z_level)
        self.down_z_button = tkinter.Button(self.z_button_frame, text='  -  ', command=self.down_z_level)
        self.z_button_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.z_level_label.grid(row=0, column=0)
        self.up_z_button.grid(row=0, column=1)
        self.down_z_button.grid(row=0, column=2)
        self.cur_z_level_label.grid(row=1, columnspan=3)

        # self.tile_style_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        # self.tile_style_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=1)
        # self.tile_options_frame = tkinter.Frame(self.menu, relief=tkinter.RIDGE, borderwidth=3)
        # self.tile_options_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=1)

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

        for i, tile in enumerate(tile_types.values()):
            tile_button = tkinter.Button(self.tile_select_frame, image=tile.appearance,
                                         command=self.set_tile(tile))
            tile_button_name = tkinter.Label(self.tile_select_frame, text=tile.name)
            tile_button.grid(row=i + 1, column=0)
            tile_button_name.grid(row=i + 1, column=1)

        self.canvas = tkinter.Canvas(tk, background=self.background_color)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_move)
        self.canvas.bind("<ButtonRelease-1>", self.place_tile)
        self.canvas.bind("<Button-3>", self.rotate_tile)
        self.canvas.pack(fill=tkinter.BOTH, expand=1)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        tk.bind("<Configure>", self.on_config)

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
        if self.z_level in self.tile_data_dict:  # To prevent the defaultdict behaviour from creating an empty level if
                                                 # it's not there
            for pos, tile in self.tile_data_dict[self.z_level].items():
                id_ = self.canvas.create_image((pos[0] * tiles.size, pos[1] * tiles.size), image=tile.rotated_appearance(),
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
        self.mouse_click_pos = tools.Object(x=event.x, y=event.y)
        self.canvas.scan_mark(event.x, event.y)

    def canvas_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.canvas_tile_grid()

    def place_tile(self, event):
        if (self.mouse_click_pos.x - event.x) ** 2 + (self.mouse_click_pos.y - event.y) ** 2 < self.place_tol ** 2:
            grid_loc = self.click_to_grid(event)
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
                id_ = self.canvas.create_image((grid_loc.x, grid_loc.y), image=self.current_tile.appearance,
                                               anchor=tkinter.NW)
                self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)] = id_
                self.place_start_pos_marker()
                self.tile_data_dict[self.z_level][(grid_loc.tile_x, grid_loc.tile_y)].set(self.current_tile)
            self.canvas_tile_grid()

    def rotate_tile(self, event):
        grid_loc = self.click_to_grid(event)
        tile = self.tile_data_dict[self.z_level][(grid_loc.tile_x, grid_loc.tile_y)]
        if tile.tile_type.can_rotate:
            tile.next_rotate()
            self.canvas.delete(self.canvas_images[(grid_loc.tile_x, grid_loc.tile_y)])
            id_ = self.canvas.create_image((grid_loc.x, grid_loc.y), image=tile.rotated_appearance(), anchor=tkinter.NW)
            self.canvas_images[(grid_loc.x, grid_loc.y)] = id_
            self.canvas_tile_grid()

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

    def save(self):
        try:
            map_name, tile_data = self.check_can_save()
        except SaveException:
            # produce an error message
            pass
        else:
            start_pos = (self.start_pos.x, self.start_pos.y, self.start_pos.z)
            print(tile_data)
            print(map_name)
            print(start_pos)

    def check_can_save(self):
        if self.start_pos is None:
            raise SaveException

        map_name = self.level_name_entry.get().strip()
        if not map_name:
            raise SaveException

        tile_data = {key: {key_: val_.to_json() for key_, val_ in val.items()}
                     for key, val in self.tile_data_dict.items()}
        if not tile_data:
            raise SaveException

        if self.start_pos.z not in tile_data:
            raise SaveException
        if (self.start_pos.x, self.start_pos.y) not in tile_data[self.start_pos.z]:
            raise SaveException

        return map_name, tile_data


if __name__ == '__main__':
    # app reference to prevent garbage collection
    app = MainApplication()
    tk.mainloop()
