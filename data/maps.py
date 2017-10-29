import os
import configparser
import collections

import Tools as tools

import Maze.config.config as config
import Maze.config.strings as strings


class MapsAccess(object):
    def __init__(self):
        self.map_lookup = {}
        self.setup_and_find_map_names()
        
    def setup_and_find_map_names(self):
        """Refreshes this instance's internal data storage, and returns a list of all the map names."""
        lookup = collections.OrderedDict()
        
        map_data_path = self._map_data_path()
        for dirpath, dirnames, filenames in os.walk(map_data_path):
            for filename in filenames:
                if filename.endswith('.' + config.MAP_FILE_EXTENSION):
                    file_path = os.path.join(map_data_path, filename)
                    map_names_in_file = self._get_map_names_in_file(file_path)
                    for map_name in map_names_in_file:
                        lookup[map_name] = filename
        
        self.map_lookup = lookup
        return list(lookup.keys())
        
    def get_map(self, map_name):
        """Gets the map data corresponding to a particular map."""
        
        # First go and get the raw map data
        try:
            filename = self.map_lookup[map_name]
        except KeyError:
            raise InvalidMapNameException(strings.Data.Exceptions.NO_MAP_NAME.format(map_name=map_name))
        parser = self._config_parser()
        file_path = os.path.join(self._map_data_path(), filename)
        parser.read(file_path)
        raw_map_data = parser[map_name]
        
        # Starting position of the player
        start_pos = tools.Object()
        try:
            raw_start_pos_data = raw_map_data['start_pos']
        except KeyError:
            raise InvalidMapException(strings.Data.Exceptions.NO_ENTRY(entry='start_pos'))
        start_pos_data = [x.strip() for x in raw_start_pos_data.split(',')]
        for coord in start_pos_data:
            key_val = [x.strip() for x in coord.split('=')]
            start_pos[key_val[0]] = int(key_val[1])
            
        # The tile data
        try:
            raw_tile_data = raw_map_data['map'].strip('\n')
        except KeyError:
            raise InvalidMapException(strings.Data.Exceptions.NO_ENTRY(entry='map', map_name=map_name))
        data_z_levels = raw_tile_data.split('\n\n')
        if not data_z_levels:
            raise InvalidMapDataException(strings.Data.Exceptions.MISCONFIGURED_MAP_DATA.format(map_name=map_name))
        tile_data = []
        for data_z_level in data_z_levels:
            tile_data.append([])
            y_rows = data_z_level.split('\n')
            if not y_rows:
                raise InvalidMapDataException(strings.Data.Exceptions.MISCONFIGURED_MAP_DATA.format(map_name=map_name))
            for y_row in y_rows:
                tile_data[-1].append(y_row)
                
        return tools.Object(name=map_name, start_pos=start_pos, tile_data=tile_data)

    @classmethod
    def _get_map_names_in_file(cls, file_path):
        """Gets all the map names in the specified file."""
        parser = cls._config_parser()
        parser.read(file_path)
        return parser.sections()
        
    @staticmethod
    def _map_data_path():
        """The path that the map data can be found in."""
        return os.path.join(os.path.dirname(__file__), config.MAP_FOLDER)

    @staticmethod
    def _config_parser():
        """The parser to use to read the map data."""
        return configparser.ConfigParser(delimiters=':')


class InvalidMapException(Exception):
    """Used to indicate that the map that is being read from the input file is not correctly formatted etc."""


class InvalidMapNameException(InvalidMapException):
    """Indicates that the specified map name does not exist."""


class InvalidMapDataException(InvalidMapException):
    """Indicates that it is specifically the tile data that has a problem."""
