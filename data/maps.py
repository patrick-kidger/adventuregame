import ast
import os
import Tools as tools

import Game.config.config as config
import Game.config.internal as internal

import Game.program.misc.exceptions as exceptions


_sentinel = object()


def map_names():
    map_names = []
    for dirpath, dirnames, filenames in os.walk(internal.Maps.MAP_LOC):
        for filename in filenames:
            if filename.endswith('.' + config.MAP_FILE_EXTENSION):
                map_names.append(os.path.splitext(filename)[0])
    return map_names


def get_map_data_from_map_name(map_name, tile_types):
    file_path = os.path.join(internal.Maps.MAP_LOC, map_name + '.' + config.MAP_FILE_EXTENSION)
    with open(file_path, 'r') as file:
        return _get_map_data(file, tile_types)


def get_map_data_from_file(file, tile_types):
    map_name = os.path.basename(file.name)
    map_name = os.path.splitext(map_name)[0]
    tile_data_dict, start_pos = _get_map_data(file, tile_types)
    return map_name, tile_data_dict, start_pos


def _get_map_data(file, tile_types):
    try:
        map_file_contents = file.read()
        mapdata = ast.literal_eval(map_file_contents)  # ast.literal_eval is safe to use on untrusted sources.

        # A list of constructuors of the types of tile in this map file.
        tile_types = [_deserialize_tile_type(serial_tile, tile_types) for serial_tile in mapdata['tile_types']]

        start_pos = mapdata['start_pos']
        if any(type(start_pos[i]) is not int for i in (0, 1, 2)):
            raise exceptions.MapLoadException
        start_pos = tools.Object(x=start_pos[0], y=start_pos[1], z=start_pos[2])

        tile_data = mapdata['tile_data']
        if not tile_data:
            raise exceptions.MapLoadException
        if type(tile_data) != list:
            raise exceptions.MapLoadException
        z_len = len(tile_data[0])
        y_len = len(tile_data[0][0])
        return_tile_data = []
        for z, z_level_data in enumerate(tile_data):
            if not z_level_data:
                raise exceptions.MapLoadException
            if len(z_level_data) != z_len:
                raise exceptions.MapLoadException
            if type(z_level_data) != list:
                raise exceptions.MapLoadException
            return_tile_data.append([])
            for y, y_row in enumerate(z_level_data):
                if not y_row:
                    raise exceptions.MapLoadException
                if len(y_row) != y_len:
                    raise exceptions.MapLoadException
                if type(y_row) != list:
                    raise exceptions.MapLoadException
                return_tile_data[-1].append([])
                for x, tile_index in enumerate(y_row):
                    if type(tile_index) != int:
                        raise exceptions.MapLoadException
                    return_tile_data[-1][-1].append(tile_types[tile_index](pos=tools.Object(x=x, y=y, z=z)))

    # SyntaxError from ast.literal_eval
    except (FileNotFoundError, KeyError, TypeError, ValueError, SyntaxError):
        raise exceptions.MapLoadException
    else:
        return return_tile_data, start_pos


def _deserialize_tile_type(serial, tile_types):
    """Deserializes the information about a single tile type. Returns a callback for creating the tile."""

    # First parse the data and make sure it's free from errors.
    tile_data = ast.literal_eval(serial)
    if tile_data is None:
        return lambda **kwargs: None
    def_ = tile_data['def']
    tile_type = tile_types[def_]
    if tile_type.can_rotate:
        rotation = tile_data['opts']['rotation']
        if rotation not in internal.TileRotation:
            raise exceptions.MapLoadException
    else:
        rotation = _sentinel
    if len(tile_type.appearance_filenames) != 1:
        appearance_lookup = tile_data['opts']['appearance_lookup']
        # Our save file parser, ast.literal_eval, can't handle frozensets, so we convert them to regular sets first.
        # As self.appearance_lookup is a dictionary key, it can only be a frozenset, not a set, so this change is
        # unambiguous; we'll switch it back when we load a file.
        # Nonetheless this seems a bit hacky.
        if isinstance(appearance_lookup, set):
            appearance_lookup = frozenset(appearance_lookup)
        if appearance_lookup not in tile_type.appearance_filenames.keys():
            raise exceptions.MapLoadException
    else:
        appearance_lookup = _sentinel

    # Now create a callback to create the tile.
    def callback(**kwargs):
        if appearance_lookup is not _sentinel:
            kwargs['appearance_lookup'] = appearance_lookup
        tile = tile_type(**kwargs)
        if rotation is not _sentinel:
            tile.rotation = rotation
        return tile
    return callback
