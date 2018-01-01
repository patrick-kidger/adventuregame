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
    try:
        with open(file_path, 'r') as file:
            return (map_name, *_get_map_data(file, tile_types))
    except OSError:
        raise exceptions.MapLoadException


def get_map_data_from_file(file, tile_types):
    map_name = os.path.basename(file.name)
    map_name = os.path.splitext(map_name)[0]
    tile_data_dict, start_pos = _get_map_data(file, tile_types)
    return map_name, tile_data_dict, start_pos


def _get_map_data(file, tile_types):
    try:
        map_file_contents = file.read()
        mapdata = ast.literal_eval(map_file_contents)  # ast.literal_eval is safe to use on untrusted sources.

        # A list of constructors of the types of tile in this map file.
        tile_types = [_deserialize_tile_type(serial_tile, tile_types) for serial_tile in mapdata['tile_types']]

        start_pos = mapdata['start_pos']
        if any(type(start_pos[i]) is not int for i in (0, 1, 2)):
            raise exceptions.MapLoadException
        start_pos = tools.Object(x=start_pos[0], y=start_pos[1], z=start_pos[2])

        return_tile_data = {}
        tile_data = mapdata['tile_data']
        if not tile_data:
            raise exceptions.MapLoadException
        for z, z_level_data in tile_data.items():
            if not z_level_data:
                raise exceptions.MapLoadException
            for (x, y), tile_def in z_level_data.items():
                if any(type(i) is not int for i in (x, y, z)):
                    raise exceptions.MapLoadException
                return_tile_data.setdefault(z, {})[(x, y)] = tile_types[tile_def](pos=tools.Object(x=x, y=y, z=z))

    # SyntaxError from ast.literal_eval
    except (KeyError, TypeError, ValueError, SyntaxError) as e:
        raise exceptions.MapLoadException from e
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
    if len(tile_type.appearances) != 1:
        appearance_lookup = tile_data['opts']['appearance_lookup']
        if appearance_lookup not in tile_type.appearance_filenames.keys():
            raise exceptions.MapLoadException
    else:
        appearance_lookup = _sentinel

    # Now create a callback to create the tile.
    def callback(**kwargs):
        if appearance_lookup is not _sentinel:
            kwargs['appearance_lookup'] = appearance_lookup
        if rotation is not _sentinel:
            kwargs['rotation'] = rotation
        tile = tile_type(**kwargs)
        return tile
    return callback
